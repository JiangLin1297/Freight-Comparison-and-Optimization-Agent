"""
Agentic工具调用框架
定义和管理可供LLM调用的工具函数
"""
import json
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter]
    function: Callable


class ToolManager:
    """工具管理器 - 管理和执行工具"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def register_tool(self, tool: ToolDefinition):
        """注册工具"""
        self.tools[tool.name] = tool
        print(f"注册工具: {tool.name}")

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的JSON Schema（用于LLM）"""
        schemas = []
        for tool in self.tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            for param in tool.parameters:
                param_schema = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    param_schema["enum"] = param.enum
                schema["parameters"]["properties"][param.name] = param_schema
                if param.required:
                    schema["parameters"]["required"].append(param.name)
            schemas.append(schema)
        return schemas

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}",
                "available_tools": list(self.tools.keys())
            }

        tool = self.tools[tool_name]

        try:
            # 验证必需参数
            for param in tool.parameters:
                if param.required and param.name not in parameters:
                    return {
                        "success": False,
                        "error": f"缺少必需参数: {param.name}",
                        "required_parameters": [p.name for p in tool.parameters if p.required]
                    }

            # 执行工具函数
            result = await tool.function(**parameters)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }


# ============================================================
# 具体工具实现
# ============================================================

async def compare_freight_tool(
    weight: float,
    orig_port: str,
    dest_port: str,
    max_days: Optional[int] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    执行运费比价查询
    根据重量、起运港、目的港等条件匹配承运商方案
    """
    from main import freight_service
    from models import OrderRequest

    order = OrderRequest(
        weight=weight,
        orig_port=orig_port,
        dest_port=dest_port,
        max_days=max_days,
        priority=priority
    )
    result = freight_service.compare(order)

    # 格式化返回结果
    plans_data = []
    for plan in result.available_plans:
        plans_data.append({
            "carrier": plan.carrier,
            "mode": "空运" if plan.mode == "AIR" else "陆运",
            "service_level": "门到门" if plan.service_level == "DTD" else "门到港",
            "transport_days": plan.transport_days,
            "total_cost": plan.total_cost,
            "service_rating": plan.service_rating,
            "score": plan.score
        })

    recommendation = None
    if result.recommended_plan:
        recommendation = {
            "carrier": result.recommended_plan.plan.carrier,
            "transport_days": result.recommended_plan.plan.transport_days,
            "total_cost": result.recommended_plan.plan.total_cost,
            "score": result.recommended_plan.plan.score,
            "reason": result.recommended_plan.reason
        }

    return {
        "total_plans": result.total_plans_found,
        "filtered_by_time": result.filtered_by_time,
        "scoring_weights": result.scoring_weights,
        "plans": plans_data,
        "recommendation": recommendation
    }


async def get_ports_tool() -> Dict[str, Any]:
    """获取所有可用的起运港和目的港列表"""
    from main import freight_service
    ports = freight_service.get_available_ports()
    return {
        "orig_ports": ports["orig_ports"],
        "dest_ports": ports["dest_ports"],
        "total_orig_ports": len(ports["orig_ports"]),
        "total_dest_ports": len(ports["dest_ports"])
    }


async def get_statistics_tool() -> Dict[str, Any]:
    """获取系统数据统计信息，包括承运商数量、报价记录数等"""
    from main import freight_service
    stats = freight_service.get_statistics()
    return {
        "total_records": stats["total_records"],
        "carriers": stats["carriers"],
        "total_carriers": len(stats["carriers"]),
        "orig_ports": stats["orig_ports"],
        "dest_ports": stats["dest_ports"],
        "transport_modes": stats["transport_modes"],
        "service_levels": stats["service_levels"]
    }


async def export_report_tool(
    weight: float,
    orig_port: str,
    dest_port: str,
    max_days: Optional[int] = None
) -> Dict[str, Any]:
    """生成并导出比价报告"""
    from main import freight_service, generate_report
    from models import OrderRequest

    order = OrderRequest(
        weight=weight,
        orig_port=orig_port,
        dest_port=dest_port,
        max_days=max_days
    )
    result = freight_service.compare(order)
    report = generate_report(result)

    return {
        "report": report,
        "total_plans": result.total_plans_found,
        "recommendation": result.recommended_plan.plan.carrier if result.recommended_plan else None
    }


async def explain_cost_tool(
    rate: float,
    min_cost: float,
    weight: float
) -> Dict[str, Any]:
    """
    解释运费计算规则
    Cost = max(Min_Cost, Rate × Weight)
    """
    calculated_cost = rate * weight
    final_cost = max(min_cost, calculated_cost)

    explanation = {
        "formula": "Cost = max(Min_Cost, Rate × Weight)",
        "inputs": {
            "rate": rate,
            "min_cost": min_cost,
            "weight": weight
        },
        "calculation": {
            "rate_times_weight": round(calculated_cost, 2),
            "min_cost": min_cost,
            "final_cost": round(final_cost, 2)
        },
        "explanation": f"计算过程：{rate} × {weight} = {calculated_cost:.2f}，"
                      f"最低费用为 {min_cost}，"
                      f"取两者最大值 = {final_cost:.2f}"
    }

    return explanation


async def compare_carriers_tool(
    carriers: List[str],
    orig_port: str,
    dest_port: str,
    weight: float
) -> Dict[str, Any]:
    """
    比较指定承运商的方案
    """
    from main import freight_service
    from models import OrderRequest

    order = OrderRequest(
        weight=weight,
        orig_port=orig_port,
        dest_port=dest_port
    )
    result = freight_service.compare(order)

    # 筛选指定承运商
    filtered_plans = [
        plan for plan in result.available_plans
        if plan.carrier in carriers
    ]

    if not filtered_plans:
        return {
            "error": f"未找到承运商 {carriers} 的方案",
            "available_carriers": list(set(plan.carrier for plan in result.available_plans))
        }

    # 格式化比较结果
    comparison = []
    for plan in filtered_plans:
        comparison.append({
            "carrier": plan.carrier,
            "mode": "空运" if plan.mode == "AIR" else "陆运",
            "transport_days": plan.transport_days,
            "total_cost": plan.total_cost,
            "service_rating": plan.service_rating,
            "score": plan.score
        })

    # 按评分排序
    comparison.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "compared_carriers": carriers,
        "plans": comparison,
        "best": comparison[0] if comparison else None
    }


# ============================================================
# 初始化工具管理器
# ============================================================

def setup_tools() -> ToolManager:
    """设置并注册所有工具"""
    manager = ToolManager()

    # 注册比价工具
    manager.register_tool(ToolDefinition(
        name="compare_freight",
        description="执行运费比价查询，根据重量、起运港、目的港等条件匹配承运商方案，返回所有可用方案和推荐方案",
        parameters=[
            ToolParameter(name="weight", type="number", description="货物重量(kg)", required=True),
            ToolParameter(name="orig_port", type="string", description="起运港代码（如 PORT08）", required=True),
            ToolParameter(name="dest_port", type="string", description="目的港代码（如 PORT09）", required=True),
            ToolParameter(name="max_days", type="integer", description="最大运输天数（可选）", required=False),
            ToolParameter(
                name="priority",
                type="string",
                description="优先级：time=时间优先，cost=成本优先",
                required=False,
                enum=["time", "cost"]
            ),
        ],
        function=compare_freight_tool
    ))

    # 注册港口工具
    manager.register_tool(ToolDefinition(
        name="get_ports",
        description="获取所有可用的起运港和目的港列表",
        parameters=[],
        function=get_ports_tool
    ))

    # 注册统计工具
    manager.register_tool(ToolDefinition(
        name="get_statistics",
        description="获取系统数据统计信息，包括承运商数量、报价记录数、港口列表等",
        parameters=[],
        function=get_statistics_tool
    ))

    # 注册导出工具
    manager.register_tool(ToolDefinition(
        name="export_report",
        description="生成并导出比价报告，包含详细的方案列表和推荐理由",
        parameters=[
            ToolParameter(name="weight", type="number", description="货物重量(kg)", required=True),
            ToolParameter(name="orig_port", type="string", description="起运港代码", required=True),
            ToolParameter(name="dest_port", type="string", description="目的港代码", required=True),
            ToolParameter(name="max_days", type="integer", description="最大运输天数（可选）", required=False),
        ],
        function=export_report_tool
    ))

    # 注册成本解释工具
    manager.register_tool(ToolDefinition(
        name="explain_cost",
        description="解释运费计算规则和计算过程，帮助用户理解费用构成",
        parameters=[
            ToolParameter(name="rate", type="number", description="费率($/kg)", required=True),
            ToolParameter(name="min_cost", type="number", description="最低费用($)", required=True),
            ToolParameter(name="weight", type="number", description="货物重量(kg)", required=True),
        ],
        function=explain_cost_tool
    ))

    # 注册承运商比较工具
    manager.register_tool(ToolDefinition(
        name="compare_carriers",
        description="比较指定承运商的方案，用于用户想了解特定承运商的对比情况",
        parameters=[
            ToolParameter(
                name="carriers",
                type="array",
                description="要比较的承运商列表（如 ['V444_0', 'V444_2']）",
                required=True
            ),
            ToolParameter(name="orig_port", type="string", description="起运港代码", required=True),
            ToolParameter(name="dest_port", type="string", description="目的港代码", required=True),
            ToolParameter(name="weight", type="number", description="货物重量(kg)", required=True),
        ],
        function=compare_carriers_tool
    ))

    return manager
