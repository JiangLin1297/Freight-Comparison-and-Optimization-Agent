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
    system_prompt: Optional[str] = None
    session_id: Optional[str] = None


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


@app.get("/api/cache_stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    return freight_service.get_cache_stats()


@app.post("/api/compare", response_model=ComparisonResult)
async def compare_freight(order: OrderRequest):
    """执行运费比价"""
    try:
        result = freight_service.compare(order)
        return result
    except Exception as e:
        # 【优化4】将Pydantic原始报错转换为友好的错误信息
        error_msg = str(e)
        if "greater_than" in error_msg:
            raise HTTPException(status_code=400, detail="参数错误：货物重量必须大于0，请检查输入")
        elif "valid_ports" in error_msg or "PORT" in error_msg:
            raise HTTPException(status_code=400, detail="参数错误：港口代码无效，请使用有效的PORT代码")
        else:
            raise HTTPException(status_code=500, detail=f"系统错误：{error_msg}")


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
    Agentic 对话接口 v3 — LLM 主导解析 + 多轮槽位补全

    主路径: parse_agent_intent (LLM) → 意图路由 → 工具调用 / 推荐 / 追问
    Fallback: classify_intent (静态正则) 在 LLM 不可用/失败时使用

    返回统一结构:
    {
      "reply_type": "clarification | recommendation | no_result | error | general",
      "message": "面向用户的自然语言回复",
      "intent": "...",
      "missing_fields": [...],
      "order": {...},
      "recommendation": {...} | null,
      "plans": [...],
      "next_actions": [...],
      "tool_calls": [...], "tool_results": [...],    // 向后兼容
      "response": "...",                              // 向后兼容
      "session_id": "...",
      "parse_source": "llm | fallback",
    }
    """
    from models import (
        AgenticOrderInfo, AgenticChatResponse,
        RecommendationSummary, PlanSummary,
        OrderRequest
    )

    # ---- 兜底: LLM 服务对象未初始化 ----
    if llm_service is None:
        return {
            "reply_type": "error",
            "message": "LLM服务未配置，请在 .env 文件中填写 DASHSCOPE_API_KEY",
            "intent": "general",
            "missing_fields": [], "order": None,
            "recommendation": None, "plans": [],
            "next_actions": ["配置 API Key 后重试"],
            "response": "LLM服务未配置",
            "tool_calls": [], "tool_results": [],
            "model": "none", "configured": False,
            "session_id": None, "parse_source": "fallback"
        }

    try:
        # ================================================================
        # 阶段 0: 多轮上下文恢复
        # ================================================================
        partial_order = None
        session = None
        if request.session_id and request.session_id in llm_service.sessions:
            session = llm_service.sessions[request.session_id]
            partial_order = session.partial_data if session.partial_data else None

        # ================================================================
        # 阶段 1: LLM 主导意图解析（含 fallback 链）
        # ================================================================
        classification = llm_service.parse_agent_intent(
            message=request.message,
            session_id=request.session_id,
            partial_order=partial_order,
        )

        intent = classification["intent"]
        order = classification["order"]
        missing = classification.get("missing_fields", [])
        parse_source = classification.get("parse_source", "fallback")
        llm_message = classification.get("message", "")

        # 构建 order 对象
        order_info = AgenticOrderInfo(
            weight=order.get("weight"),
            orig_port=order.get("orig_port"),
            dest_port=order.get("dest_port"),
            max_days=order.get("max_days"),
            priority=order.get("priority"),
        )

        # ================================================================
        # 阶段 2: 多轮会话管理
        # ================================================================
        new_session_id = request.session_id

        def _save_session():
            """将当前解析状态保存到会话（用于多轮追问）"""
            nonlocal new_session_id, session
            if new_session_id and new_session_id in llm_service.sessions:
                session = llm_service.sessions[new_session_id]
            else:
                import uuid
                new_session_id = str(uuid.uuid4())
                from llm_service import ConversationSession
                session = ConversationSession(session_id=new_session_id)
                llm_service.sessions[new_session_id] = session

            session.current_state = "parsing"
            session.partial_data = {
                "weight": order.get("weight"),
                "orig_port": order.get("orig_port"),
                "dest_port": order.get("dest_port"),
                "max_days": order.get("max_days"),
                "priority": order.get("priority"),
            }
            session.missing_fields = list(missing)
            session.user_feedback = llm_message

        def _clear_session():
            """信息完整后清理会话"""
            nonlocal new_session_id
            if new_session_id and new_session_id in llm_service.sessions:
                llm_service.sessions[new_session_id].current_state = "completed"

        # ================================================================
        # 阶段 3: 根据意图和缺失字段路由
        # ================================================================

        # ---- 3a: compare_freight 但缺字段 → clarification ----
        if intent == "compare_freight" and missing:
            _save_session()

            field_cn = {"weight": "货物重量", "orig_port": "起运港", "dest_port": "目的港"}
            missing_cn = [field_cn.get(f, f) for f in missing]
            known_parts = []
            if order["weight"]: known_parts.append(f"{order['weight']}kg")
            if order["orig_port"]: known_parts.append(f"起运港 {order['orig_port']}")
            if order["dest_port"]: known_parts.append(f"目的港 {order['dest_port']}")
            if order["max_days"]: known_parts.append(f"{order['max_days']}天内")

            if known_parts:
                message = f"已收到您的运输需求：{'，'.join(known_parts)}。\n\n还需要补充：{'、'.join(missing_cn)}。\n\n例如：从上海运100kg到深圳，5天内到达。"
            else:
                message = f"您好！请提供运输需求信息：{'、'.join(missing_cn)}。\n\n例如：从上海运100kg到深圳，5天内到达。"

            if llm_message and llm_message != message:
                message = llm_message  # 优先使用 LLM 生成的自然语言消息

            return {
                "reply_type": "clarification",
                "message": message,
                "intent": intent,
                "missing_fields": missing,
                "order": order_info.dict() if order_info else None,
                "recommendation": None, "plans": [],
                "next_actions": [f"请提供{'、'.join(missing_cn)}"],
                "response": message,
                "tool_calls": [], "tool_results": [],
                "model": llm_service.model, "configured": True,
                "session_id": new_session_id, "parse_source": parse_source
            }

        # ---- 3b: compare_freight 信息完整 → 执行比价 ----
        if intent == "compare_freight" and not missing:
            _clear_session()

            try:
                freight_order = OrderRequest(
                    weight=order["weight"],
                    orig_port=order["orig_port"],
                    dest_port=order["dest_port"],
                    max_days=order.get("max_days"),
                    priority=order.get("priority")
                )
            except Exception:
                return {
                    "reply_type": "error",
                    "message": f"订单参数无效：重量必须大于0，港口代码需在PORT02-PORT11范围内",
                    "intent": intent,
                    "missing_fields": missing,
                    "order": order_info.dict() if order_info else None,
                    "recommendation": None, "plans": [],
                    "next_actions": ["检查港口代码是否正确", "确认重量大于0"],
                    "response": "订单参数无效",
                    "tool_calls": [], "tool_results": [],
                    "model": llm_service.model, "configured": True,
                    "session_id": new_session_id, "parse_source": parse_source
                }

            result = freight_service.compare(freight_order)

            # 构建 plans 列表
            plans_data = []
            for plan in result.available_plans[:5]:
                plans_data.append(PlanSummary(
                    carrier=plan.carrier,
                    mode="空运" if plan.mode == "AIR" else "陆运",
                    service_level="门到门" if plan.service_level == "DTD" else "门到港",
                    transport_days=plan.transport_days,
                    total_cost=plan.total_cost,
                    service_rating=plan.service_rating,
                    score=plan.score
                ).dict())

            # ---- 3b-i: 有推荐方案 → recommendation ----
            if result.recommended_plan:
                rp = result.recommended_plan.plan
                rec = RecommendationSummary(
                    carrier=rp.carrier,
                    transport_days=rp.transport_days,
                    total_cost=rp.total_cost,
                    mode="空运" if rp.mode == "AIR" else "陆运",
                    service_level="门到门" if rp.service_level == "DTD" else "门到港",
                    service_rating=rp.service_rating,
                    score=rp.score,
                    reason=result.recommended_plan.reason
                )

                # ---- LLM 反馈生成（阶段2） ----
                fb = llm_service.generate_agent_feedback(
                    user_message=request.message,
                    order=order,
                    recommendation=rec.dict(),
                    plans=plans_data,
                    total_plans_found=result.total_plans_found,
                    scoring_weights=result.scoring_weights,
                    reply_type="recommendation",
                    intent=intent,
                    parse_source=parse_source,
                    next_actions=[],
                )
                message = fb["message"]
                feedback_source = fb["feedback_source"]
                feedback_reason = fb["feedback_reason"]

                next_actions = [
                    "查看全部方案详情",
                    "导出比价报告",
                    "调整时效要求重新查询" if not order.get("max_days") else "放宽时效要求重新查询"
                ]

                return {
                    "reply_type": "recommendation",
                    "message": message,
                    "feedback_source": feedback_source,
                    "feedback_reason": feedback_reason,
                    "intent": intent,
                    "missing_fields": [],
                    "order": order_info.dict() if order_info else None,
                    "recommendation": rec.dict(),
                    "plans": plans_data,
                    "next_actions": next_actions,
                    "response": message,
                    "tool_calls": [{"tool": "compare_freight", "parameters": {
                        "weight": order["weight"], "orig_port": order["orig_port"],
                        "dest_port": order["dest_port"],
                        "max_days": order.get("max_days"), "priority": order.get("priority")
                    }}],
                    "tool_results": [{"success": True, "tool": "compare_freight",
                                    "total_plans": result.total_plans_found}],
                    "model": llm_service.model, "configured": True,
                    "session_id": new_session_id, "parse_source": parse_source
                }

            # ---- 3b-ii: 无方案 → no_result ----
            else:
                route_str = f"{order['orig_port']} -> {order['dest_port']}"
                has_time_filter = order.get("max_days") is not None

                if has_time_filter:
                    no_result_reason = f"在 {order['max_days']} 天时效内，{route_str} 路线无可用方案"
                    next_actions = [
                        f"尝试放宽时效要求至 {order['max_days'] + 3} 天",
                        "选择空运方式",
                        "查询其他港口组合"
                    ]
                else:
                    no_result_reason = f"{route_str} 路线暂无可用方案"
                    next_actions = [
                        "尝试其他目的港",
                        "调整货物重量",
                        "联系客服获取更多方案"
                    ]

                # ---- LLM 反馈生成（阶段2） ----
                fb = llm_service.generate_agent_feedback(
                    user_message=request.message,
                    order=order,
                    recommendation=None,
                    plans=[],
                    total_plans_found=0,
                    scoring_weights=None,
                    reply_type="no_result",
                    intent=intent,
                    parse_source=parse_source,
                    no_result_reason=no_result_reason,
                    next_actions=next_actions,
                )

                return {
                    "reply_type": "no_result",
                    "message": fb["message"],
                    "intent": intent,
                    "missing_fields": [],
                    "order": order_info.dict() if order_info else None,
                    "recommendation": None, "plans": [],
                    "next_actions": next_actions,
                    "response": fb["message"],
                    "tool_calls": [{"tool": "compare_freight", "parameters": {
                        "weight": order["weight"], "orig_port": order["orig_port"],
                        "dest_port": order["dest_port"],
                        "max_days": order.get("max_days"), "priority": order.get("priority")
                    }}],
                    "tool_results": [{"success": True, "tool": "compare_freight",
                                    "total_plans": 0}],
                    "model": llm_service.model, "configured": True,
                    "session_id": new_session_id, "parse_source": parse_source,
                    "feedback_source": fb["feedback_source"],
                    "feedback_reason": fb["feedback_reason"],
                }

        # ---- 3c: get_ports / get_statistics → 直接调工具 ----
        if intent in ("get_ports", "get_statistics"):
            _clear_session()
            tool_name = intent
            try:
                tool_result = await tool_manager.execute_tool(tool_name, {})
            except Exception:
                tool_result = {"success": False, "tool": tool_name, "error": "工具执行失败"}

            if tool_result.get("success"):
                if intent == "get_ports":
                    data = tool_result["result"]
                    message = (
                        f"可用港口信息：\n\n"
                        f"起运港（{data.get('total_orig_ports', 0)}个）：\n"
                        f"{', '.join(data.get('orig_ports', []))}\n\n"
                        f"目的港（{data.get('total_dest_ports', 0)}个）：\n"
                        f"{', '.join(data.get('dest_ports', []))}\n\n"
                        f"您可以输入'从[起运港]运[重量]到[目的港]'来查询运费方案。"
                    )
                else:
                    data = tool_result["result"]
                    message = (
                        f"系统数据统计：\n\n"
                        f"总报价记录：{data.get('total_records', 0)} 条\n"
                        f"承运商数量：{data.get('total_carriers', 0)} 家\n"
                        f"运输方式：{', '.join(data.get('transport_modes', []))}\n"
                        f"服务级别：{', '.join(data.get('service_levels', []))}"
                    )

                return {
                    "reply_type": "general",
                    "message": message,
                    "intent": intent,
                    "missing_fields": [], "order": None,
                    "recommendation": None, "plans": [],
                    "next_actions": ["输入运输需求查询运费方案"],
                    "response": message,
                    "tool_calls": [{"tool": tool_name, "parameters": {}}],
                    "tool_results": [tool_result],
                    "model": llm_service.model, "configured": True,
                    "session_id": new_session_id, "parse_source": parse_source
                }
            else:
                return {
                    "reply_type": "error",
                    "message": f"查询失败：{tool_result.get('error', '未知错误')}",
                    "intent": intent,
                    "missing_fields": [], "order": None,
                    "recommendation": None, "plans": [],
                    "next_actions": ["重试查询"],
                    "response": "查询失败",
                    "tool_calls": [], "tool_results": [tool_result],
                    "model": llm_service.model, "configured": True,
                    "session_id": new_session_id, "parse_source": parse_source
                }

        # ---- 3d: explain_cost / export_report / compare_carriers → LLM工具调用 ----
        if intent in ("explain_cost", "export_report", "compare_carriers"):
            _clear_session()
            llm_result = llm_service.chat_with_tools(request.message)
            tool_calls = llm_result.get("tool_calls", [])
            tool_results = []
            if tool_calls and tool_manager:
                for tc in tool_calls:
                    try:
                        tr = await tool_manager.execute_tool(tc.get("tool"), tc.get("parameters", {}))
                        tool_results.append(tr)
                    except Exception as e:
                        tool_results.append({"success": False, "tool": tc.get("tool"), "error": str(e)})

            return {
                "reply_type": "general",
                "message": llm_result.get("response", ""),
                "intent": intent,
                "missing_fields": missing,
                "order": order_info.dict() if order_info else None,
                "recommendation": None, "plans": [],
                "next_actions": [],
                "response": llm_result.get("response", ""),
                "tool_calls": tool_calls, "tool_results": tool_results,
                "model": llm_service.model, "configured": True,
                "session_id": llm_result.get("session_id"), "parse_source": parse_source
            }

        # ---- 3e: general 闲聊 → LLM 直接对话 ----
        _clear_session()
        llm_result = llm_service.chat_with_tools(request.message)
        tool_calls = llm_result.get("tool_calls", [])
        tool_results = []
        if tool_calls and tool_manager:
            for tc in tool_calls:
                try:
                    tr = await tool_manager.execute_tool(tc.get("tool"), tc.get("parameters", {}))
                    tool_results.append(tr)
                except Exception as e:
                    tool_results.append({"success": False, "tool": tc.get("tool"), "error": str(e)})

        return {
            "reply_type": "general",
            "message": llm_result.get("response", ""),
            "intent": "general",
            "missing_fields": [], "order": None,
            "recommendation": None, "plans": [],
            "next_actions": ["输入运输需求开始查询，例如：从大连运100kg到厦门"],
            "response": llm_result.get("response", ""),
            "tool_calls": tool_calls, "tool_results": tool_results,
            "model": llm_service.model, "configured": True,
            "session_id": llm_result.get("session_id"), "parse_source": parse_source
        }

    except Exception as e:
        return {
            "reply_type": "error",
            "message": f"处理请求时发生错误：{str(e)}",
            "intent": "general",
            "missing_fields": [], "order": None,
            "recommendation": None, "plans": [],
            "next_actions": ["重试请求", "检查输入格式"],
            "response": f"处理失败: {str(e)}",
            "tool_calls": [], "tool_results": [], "error": str(e),
            "model": llm_service.model if llm_service else "none",
            "configured": llm_service.is_configured() if llm_service else False,
            "session_id": None, "parse_source": "fallback"
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
