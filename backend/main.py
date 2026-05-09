from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from models import OrderRequest, ComparisonResult
from freight_service import FreightService

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

# 初始化服务
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates.csv")
freight_service = FreightService(DATA_PATH)

# 挂载前端静态文件
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_PATH):
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")


@app.get("/")
async def root():
    """返回前端页面"""
    index_path = os.path.join(FRONTEND_PATH, "index.html")
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
    return freight_service.get_statistics()


@app.post("/api/compare", response_model=ComparisonResult)
async def compare_freight(order: OrderRequest):
    """
    执行运费比价

    - **weight**: 货物总重量(kg)
    - **orig_port**: 起运港代码
    - **dest_port**: 目的港代码
    - **max_days**: 最大运输天数(可选)
    """
    try:
        result = freight_service.compare(order)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export")
async def export_report(order: OrderRequest):
    """导出比价报告"""
    try:
        result = freight_service.compare(order)
        report = generate_report(result)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
