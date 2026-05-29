from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

# 手动加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from models import OrderRequest, ComparisonResult
from freight_service import FreightService, CSVDataStore

# 工具管理器导入
try:
    from tools import setup_tools, ToolManager
    tool_manager = setup_tools()
    print(f"工具管理器初始化成功，已注册 {len(tool_manager.tools)} 个工具")
except Exception as e:
    print(f"工具管理器初始化失败: {e}")
    tool_manager = None

# LLM服务可选导入
try:
    from llm_service import LLMService
    llm_service = LLMService(tool_manager=tool_manager)
except Exception as e:
    print(f"LLM服务初始化失败: {e}")
    llm_service = None

app = FastAPI(
    title="运输方案比价与优化智能体",
    description="根据订单信息自动匹配承运商报价，完成运费核算和多方案比价",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 使用CSV数据源（优先使用带评级的数据文件）
DATA_PATH_WITH_RATING = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates_with_rating.csv")
DATA_PATH_ORIGINAL = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates.csv")
DATA_PATH_EXTENDED = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates_extended.csv")
DATA_PATH_COMBINED = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates_combined.csv")

# 优先使用合并数据（包含扩展数据）
if os.path.exists(DATA_PATH_COMBINED):
    DATA_PATH = DATA_PATH_COMBINED
    print(f"使用合并 CSV 数据源: {DATA_PATH}")
elif os.path.exists(DATA_PATH_WITH_RATING):
    DATA_PATH = DATA_PATH_WITH_RATING
    print(f"使用带评级的 CSV 数据源: {DATA_PATH}")
else:
    DATA_PATH = DATA_PATH_ORIGINAL
    print(f"使用原始 CSV 数据源: {DATA_PATH}")

# 加载数据（如果存在扩展数据，会自动合并）
data_store = CSVDataStore(DATA_PATH, DATA_PATH_EXTENDED if DATA_PATH != DATA_PATH_EXTENDED else None)

freight_service = FreightService(data_store)


class ChatRequest(BaseModel):
    message: str
    system_prompt: str = None


class ParseRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


class ContinueRequest(BaseModel):
    session_id: str
    message: str


# 挂载前端静态文件
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(STATIC_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_PATH, "assets")), name="assets")
    SERVE_PATH = STATIC_PATH
elif os.path.exists(FRONTEND_PATH):
    SERVE_PATH = FRONTEND_PATH
else:
    SERVE_PATH = None


@app.get("/")
async def root():
    """返回前端页面"""
    if SERVE_PATH:
        index_path = os.path.join(SERVE_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "运输方案比价与优化智能体 API"}


@app.get("/api/ports")
async def get_ports():
    """获取可用港口列表"""
    return freight_service.get_available_ports()


@app.get("/api/statistics")
async def get_statistics():
    """获取数据统计信息"""
    stats = freight_service.get_statistics()
    stats["data_source"] = "csv"
    return stats


@app.post("/api/compare", response_model=ComparisonResult)
async def compare_freight(order: OrderRequest):
    """执行运费比价"""
    try:
        result = freight_service.compare(order)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """调用 LLM 进行对话"""
    if llm_service is None:
        return {"response": "LLM服务未配置", "model": "none", "configured": False}
    response = llm_service.chat(request.message, request.system_prompt)
    return {"response": response, "model": llm_service.model, "configured": llm_service.is_configured()}


@app.post("/api/agentic_chat")
async def agentic_chat(request: ChatRequest):
    """
    Agentic对话接口 - 支持工具调用
    LLM会根据用户输入自动选择和调用合适的工具
    """
    if llm_service is None:
        return {"response": "LLM服务未配置", "tool_calls": [], "configured": False}

    try:
        # 获取LLM响应和工具调用
        llm_result = llm_service.chat_with_tools(request.message)
        tool_calls = llm_result.get("tool_calls", [])

        # 执行工具调用
        tool_results = []
        if tool_calls and tool_manager:
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})

                try:
                    tool_result = await tool_manager.execute_tool(tool_name, parameters)
                    tool_results.append(tool_result)
                except Exception as e:
                    tool_results.append({
                        "success": False,
                        "tool": tool_name,
                        "error": str(e)
                    })

        return {
            "response": llm_result.get("response", ""),
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "model": llm_service.model if llm_service else "none",
            "configured": llm_result.get("configured", False),
            "session_id": llm_result.get("session_id")
        }

    except Exception as e:
        return {
            "response": f"处理失败: {str(e)}",
            "tool_calls": [],
            "tool_results": [],
            "error": str(e)
        }


@app.get("/api/tools")
async def get_tools():
    """获取所有可用工具列表"""
    if tool_manager is None:
        return {"tools": [], "count": 0}
    return {
        "tools": tool_manager.get_tools_schema(),
        "count": len(tool_manager.tools)
    }


@app.post("/api/execute_tool")
async def execute_tool(tool_name: str, parameters: dict = {}):
    """直接执行指定工具"""
    if tool_manager is None:
        raise HTTPException(status_code=500, detail="工具管理器未初始化")
    try:
        result = await tool_manager.execute_tool(tool_name, parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/parse")
async def parse_order(request: ParseRequest):
    """将自然语言描述解析为结构化订单数据，支持CoT思维链"""
    if llm_service is None:
        return {"error": "LLM服务未配置", "data": None}
    try:
        result = llm_service.parse_order(request.text, request.session_id)
        return {"error": None, "data": result}
    except Exception as e:
        return {"error": str(e), "data": None}


@app.post("/api/continue")
async def continue_conversation(request: ContinueRequest):
    """继续多轮对话，补充缺失信息"""
    if llm_service is None:
        return {"error": "LLM服务未配置", "data": None}
    try:
        result = llm_service.continue_conversation(request.session_id, request.message)
        return {"error": None, "data": result}
    except Exception as e:
        return {"error": str(e), "data": None}


@app.get("/api/session/{session_id}")
async def get_session_status(session_id: str):
    """获取会话状态"""
    if llm_service is None:
        return {"error": "LLM服务未配置", "data": None}
    try:
        result = llm_service.get_session_status(session_id)
        return {"error": None, "data": result}
    except Exception as e:
        return {"error": str(e), "data": None}


@app.post("/api/export")
async def export_report(order: OrderRequest):
    """导出比价报告"""
    try:
        result = freight_service.compare(order)
        report = generate_report(result)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "data_source": "csv",
        "llm_configured": llm_service.is_configured() if llm_service else False,
        "llm_model": llm_service.model if llm_service else "none",
    }


def generate_report(result: ComparisonResult) -> str:
    """生成比价报告文本"""
    lines = []
    lines.append("=" * 60)
    lines.append("运输方案比价报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append("【订单信息】")
    lines.append(f"  起运港: {result.order_info.orig_port}")
    lines.append(f"  目的港: {result.order_info.dest_port}")
    lines.append(f"  货物重量: {result.order_info.weight} kg")
    if result.order_info.max_days:
        lines.append(f"  时效要求: ≤{result.order_info.max_days}天")
    lines.append("")
    lines.append(f"【查询结果】共找到 {result.total_plans_found} 个可用方案")
    lines.append("")

    if result.available_plans:
        lines.append("【方案列表】")
        lines.append(f"{'承运商':<12} {'运输方式':<8} {'服务级别':<8} {'天数':<6} {'成本':<12} {'计算公式'}")
        lines.append("-" * 70)
        for plan in result.available_plans:
            mode_cn = "空运" if plan.mode == "AIR" else "陆运"
            service_cn = "门到门" if plan.service_level == "DTD" else "门到港"
            lines.append(f"{plan.carrier:<12} {mode_cn:<8} {service_cn:<8} {plan.transport_days:<6} ${plan.total_cost:<11.2f} {plan.cost_formula}")

    lines.append("")
    if result.recommended_plan:
        lines.append("【推荐方案】")
        lines.append(f"  承运商: {result.recommended_plan.plan.carrier}")
        mode_cn = "空运" if result.recommended_plan.plan.mode == "AIR" else "陆运"
        service_cn = "门到门" if result.recommended_plan.plan.service_level == "DTD" else "门到港"
        lines.append(f"  运输方式: {mode_cn}")
        lines.append(f"  服务级别: {service_cn}")
        lines.append(f"  运输天数: {result.recommended_plan.plan.transport_days}天")
        lines.append(f"  总成本: ${result.recommended_plan.plan.total_cost:.2f}")
        lines.append(f"  推荐理由: {result.recommended_plan.reason}")
    else:
        lines.append("【推荐方案】无满足条件的方案")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
