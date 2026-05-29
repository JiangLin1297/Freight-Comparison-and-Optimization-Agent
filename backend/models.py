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


class Recommendation(BaseModel):
    """推荐方案模型"""
    plan: CarrierPlan
    reason: str
    rank: int


class ComparisonResult(BaseModel):
    """比价结果模型"""
    order_info: OrderRequest
    available_plans: List[CarrierPlan]
    recommended_plan: Optional[Recommendation]
    total_plans_found: int
    filtered_by_time: bool
    scoring_weights: Optional[Dict] = Field(None, description="使用的评分权重配置")
