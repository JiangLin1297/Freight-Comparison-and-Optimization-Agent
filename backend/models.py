from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class OrderRequest(BaseModel):
    """订单请求模型"""
    weight: float = Field(..., gt=0, description="货物总重量(kg)")
    orig_port: str = Field(..., description="起运港代码")
    dest_port: str = Field(..., description="目的港代码")
    max_days: Optional[int] = Field(None, ge=0, le=365, description="最大运输天数(可选，范围0-365)")


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
