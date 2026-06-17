from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class ScoringWeights(BaseModel):
    """评分权重配置"""
    cost_weight: float = Field(0.4, ge=0, le=1, description="成本权重")
    time_weight: float = Field(0.3, ge=0, le=1, description="时效权重")
    service_weight: float = Field(0.3, ge=0, le=1, description="服务权重")


class OrderRequest(BaseModel):
    """订单请求模型"""
    weight: float = Field(..., gt=0, description="货物总重量(kg)")
    orig_port: str = Field(..., description="起运港代码")
    dest_port: str = Field(..., description="目的港代码")
    max_days: Optional[int] = Field(None, ge=0, le=365, description="最大运输天数(可选，范围0-365)")
    priority: Optional[str] = Field(None, description="优先级: 'time'(时间优先) 或 'cost'(成本优先)，默认为cost")
    weights: Optional[ScoringWeights] = Field(None, description="自定义评分权重配置")


class CarrierPlan(BaseModel):
    """承运商方案模型"""
    carrier: str
    orig_port: str
    dest_port: str
    min_weight: float
    max_weight: float
    service_level: str
    min_cost: float
    rate: float
    mode: str
    transport_days: int
    carrier_type: str
    total_cost: float
    cost_formula: str
    service_rating: Optional[str] = Field(None, description="服务评级 A/B/C/D/E")
    score: Optional[float] = Field(None, description="综合评分")
    score_details: Optional[Dict] = Field(None, description="评分明细")
    is_exact_match: bool = Field(True, description="是否精确匹配（重量在范围内）")


class Recommendation(BaseModel):
    """推荐方案模型"""
    plan: CarrierPlan
    reason: str
    rank: int


class LegPlan(BaseModel):
    """转运路线中的一段"""
    from_port: str
    to_port: str
    carrier: str
    mode: str
    service_level: str
    transport_days: int
    total_cost: float
    cost_formula: str
    service_rating: Optional[str] = None


class TransferPlan(BaseModel):
    """转运方案 (多跳路由)"""
    path: List[str]
    legs: List[LegPlan]
    total_cost: float
    total_days: int
    hop_count: int
    transfer_penalty_days: int = 1
    total_estimated_days: int = 0
    is_direct: bool = True
    route_display: str = ""
    score: Optional[float] = None                      # 综合评分 (与直达可比)
    avg_service_rating: Optional[str] = None           # 各段最低服务评级
    # 多段推荐理由
    leg_details: List[str] = Field(default_factory=list)
    recommendation_reason: str = ""


class ComparisonResult(BaseModel):
    """比价结果模型"""
    order_info: OrderRequest
    available_plans: List[CarrierPlan]
    recommended_plan: Optional[Recommendation]
    total_plans_found: int
    filtered_by_time: bool
    scoring_weights: Optional[Dict] = Field(None, description="使用的评分权重配置")
    # 转运相关字段
    has_direct_route: bool = Field(True, description="是否存在直达路线")
    transfer_routes: Optional[List[TransferPlan]] = Field(
        None, description="转运路线方案 (无直达或直达被过滤时提供)"
    )
    fallback_transfer: Optional[TransferPlan] = Field(
        None, description="次优推荐转运方案 (所有方案都不满足条件时)"
    )
    fallback_reason: str = Field(
        "", description="次优推荐原因说明"
    )


# ============================================================
# Agentic Chat v2: 统一响应结构
# ============================================================

class AgenticOrderInfo(BaseModel):
    """Agentic对话中提取的订单信息"""
    weight: Optional[float] = Field(None, description="货物重量(kg)")
    orig_port: Optional[str] = Field(None, description="起运港代码")
    dest_port: Optional[str] = Field(None, description="目的港代码")
    max_days: Optional[int] = Field(None, description="最大运输天数")
    priority: Optional[str] = Field(None, description="优先级: time/cost/null")


class PlanSummary(BaseModel):
    """方案摘要"""
    carrier: str
    mode: str
    service_level: str
    transport_days: int
    total_cost: float
    service_rating: Optional[str] = None
    score: Optional[float] = None


class RecommendationSummary(BaseModel):
    """推荐方案摘要"""
    carrier: str
    transport_days: int
    total_cost: float
    mode: str
    service_level: str
    service_rating: Optional[str] = None
    score: Optional[float] = None
    reason: str = ""


class AgenticChatResponse(BaseModel):
    """
    Agentic 对话统一响应结构（v2）
    新前端优先使用 reply_type / message / missing_fields / order / recommendation / next_actions
    旧字段 response / tool_calls / tool_results 保留向后兼容
    """
    # === 新字段（v2） ===
    reply_type: str = Field(
        "general",
        description="clarification | recommendation | no_result | error | general"
    )
    message: str = Field("", description="面向用户的自然语言回复")
    intent: str = Field("general", description="识别到的用户意图")
    missing_fields: List[str] = Field(default_factory=list, description="缺失的必要字段列表")
    order: Optional[AgenticOrderInfo] = Field(None, description="提取到的订单信息")
    recommendation: Optional[RecommendationSummary] = Field(None, description="推荐方案摘要")
    plans: List[PlanSummary] = Field(default_factory=list, description="可用方案列表（最多5条）")
    next_actions: List[str] = Field(default_factory=list, description="建议的下一步操作")

    # === 旧字段（向后兼容） ===
    response: str = Field("", description="[兼容] 旧版 response 字段")
    tool_calls: List[Dict] = Field(default_factory=list, description="[兼容] 工具调用列表")
    tool_results: List[Dict] = Field(default_factory=list, description="[兼容] 工具调用结果")

    # === 元信息 ===
    model: str = Field("", description="使用的LLM模型")
    configured: bool = Field(False, description="LLM是否已配置")
    session_id: Optional[str] = Field(None, description="会话ID")
    parse_source: str = Field("fallback", description="解析来源: llm | fallback")
