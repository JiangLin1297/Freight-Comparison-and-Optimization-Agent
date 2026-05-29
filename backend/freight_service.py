"""运费比价服务 - 使用CSV数据源，支持多维度评分"""
import os
import pandas as pd
from typing import List, Optional, Dict, Any
from models import OrderRequest, CarrierPlan, ComparisonResult, Recommendation, ScoringWeights


class CSVDataStore:
    """CSV文件数据源 - 支持多数据源合并"""

    def __init__(self, csv_path: str, extended_csv_path: str = None):
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()

        # 加载扩展数据
        if extended_csv_path and os.path.exists(extended_csv_path):
            extended_df = pd.read_csv(extended_csv_path)
            extended_df.columns = extended_df.columns.str.strip()
            self.df = pd.concat([self.df, extended_df], ignore_index=True)
            # 去重
            self.df = self.df.drop_duplicates()
            print(f"已加载扩展数据，总记录数: {len(self.df)}")

        self._clean_data()

    def _clean_data(self):
        """清洗数据"""
        self.df['Mode_DSC'] = self.df['Mode_DSC'].str.strip()
        self.df['Min_Weight_Quant'] = pd.to_numeric(self.df['Min_Weight_Quant'], errors='coerce')
        self.df['Max_Weight_Quant'] = pd.to_numeric(self.df['Max_Weight_Quant'], errors='coerce')
        self.df['Min_Cost'] = pd.to_numeric(self.df['Min_Cost'], errors='coerce')
        self.df['Rate'] = pd.to_numeric(self.df['Rate'], errors='coerce')
        self.df['TPT_Day_Count'] = pd.to_numeric(self.df['TPT_Day_Count'], errors='coerce')
        # 处理 Service_Rating 字段（如果存在）
        if 'Service_Rating' in self.df.columns:
            self.df['Service_Rating'] = self.df['Service_Rating'].fillna('C').str.strip()
        else:
            self.df['Service_Rating'] = 'C'

    def get_available_ports(self) -> dict:
        orig_ports = sorted(self.df['Orig_Port'].unique().tolist())
        dest_ports = sorted(self.df['Dest_Port'].unique().tolist())
        return {"orig_ports": orig_ports, "dest_ports": dest_ports}

    def get_statistics(self) -> dict:
        return {
            "total_records": len(self.df),
            "carriers": sorted(self.df['Carrier'].unique().tolist()),
            "orig_ports": sorted(self.df['Orig_Port'].unique().tolist()),
            "dest_ports": sorted(self.df['Dest_Port'].unique().tolist()),
            "transport_modes": sorted(self.df['Mode_DSC'].unique().tolist()),
            "service_levels": sorted(self.df['Service_Level'].unique().tolist()),
        }

    def match_plans(self, order: OrderRequest) -> List[Dict[str, Any]]:
        df = self.df
        mask = (
            (df['Orig_Port'] == order.orig_port) &
            (df['Dest_Port'] == order.dest_port) &
            (df['Min_Weight_Quant'] <= order.weight) &
            (df['Max_Weight_Quant'] >= order.weight)
        )
        matched = df[mask]

        results = []
        for _, row in matched.iterrows():
            results.append({
                "carrier": row['Carrier'],
                "orig_port": row['Orig_Port'],
                "dest_port": row['Dest_Port'],
                "min_weight": row['Min_Weight_Quant'],
                "max_weight": row['Max_Weight_Quant'],
                "service_level": row['Service_Level'],
                "min_cost": row['Min_Cost'],
                "rate": row['Rate'],
                "mode": row['Mode_DSC'],
                "transport_days": int(row['TPT_Day_Count']),
                "carrier_type": row['Carrier_Type'],
                "service_rating": row.get('Service_Rating', 'C'),
            })
        return results


class FreightService:
    """运费比价服务"""

    def __init__(self, data_store: CSVDataStore):
        self.data_store = data_store

    def get_available_ports(self) -> dict:
        return self.data_store.get_available_ports()

    def get_statistics(self) -> dict:
        return self.data_store.get_statistics()

    def calculate_cost(self, rate: float, min_cost: float, weight: float) -> float:
        """计算运输成本: Cost = max(Min_Cost, Rate * Weight)"""
        calculated_cost = rate * weight
        return max(min_cost, calculated_cost)

    def calculate_score(self, plan: CarrierPlan, all_plans: List[CarrierPlan],
                       weights: ScoringWeights) -> tuple:
        """
        计算综合评分
        Score = w1×成本归一化 + w2×时效归一化 + w3×服务评级归一化
        返回: (总分, 评分明细字典)
        """
        # 1. 成本归一化 (越低越好，使用反向归一化)
        costs = [p.total_cost for p in all_plans]
        min_cost, max_cost = min(costs), max(costs)
        if max_cost > min_cost:
            cost_score = 1 - (plan.total_cost - min_cost) / (max_cost - min_cost)
        else:
            cost_score = 1.0

        # 2. 时效归一化 (越快越好，使用反向归一化)
        days = [p.transport_days for p in all_plans]
        min_days, max_days = min(days), max(days)
        if max_days > min_days:
            time_score = 1 - (plan.transport_days - min_days) / (max_days - min_days)
        else:
            time_score = 1.0

        # 3. 服务评级归一化 (A=1.0, B=0.8, C=0.6, D=0.4, E=0.2)
        rating_map = {'A': 1.0, 'B': 0.8, 'C': 0.6, 'D': 0.4, 'E': 0.2}
        service_score = rating_map.get(plan.service_rating, 0.5)

        # 4. 加权计算
        total_score = (
            weights.cost_weight * cost_score +
            weights.time_weight * time_score +
            weights.service_weight * service_score
        )

        details = {
            'cost_score': round(cost_score, 3),
            'time_score': round(time_score, 3),
            'service_score': round(service_score, 3),
            'weights': {
                'cost': weights.cost_weight,
                'time': weights.time_weight,
                'service': weights.service_weight
            }
        }

        return round(total_score, 3), details

    def match_plans(self, order: OrderRequest) -> List[CarrierPlan]:
        """匹配承运商方案"""
        raw_plans = self.data_store.match_plans(order)
        plans = []
        for row in raw_plans:
            total_cost = self.calculate_cost(row['rate'], row['min_cost'], order.weight)
            plan = CarrierPlan(
                carrier=row['carrier'],
                orig_port=row['orig_port'],
                dest_port=row['dest_port'],
                min_weight=row['min_weight'],
                max_weight=row['max_weight'],
                service_level=row['service_level'],
                min_cost=round(row['min_cost'], 2),
                rate=round(row['rate'], 4),
                mode=row['mode'],
                transport_days=row['transport_days'],
                carrier_type=row['carrier_type'],
                total_cost=round(total_cost, 2),
                cost_formula=f"max({row['min_cost']:.2f}, {row['rate']:.4f} * {order.weight}) = {total_cost:.2f}",
                service_rating=row.get('service_rating', 'C')
            )
            plans.append(plan)
        return plans

    def recommend_plan(self, plans: List[CarrierPlan], max_days: Optional[int] = None,
                      priority: Optional[str] = None,
                      weights: Optional[ScoringWeights] = None) -> Optional[Recommendation]:
        """推荐最优方案 - 支持多维度评分"""
        if not plans:
            return None

        filtered_plans = plans
        if max_days is not None:
            filtered_plans = [p for p in plans if p.transport_days <= max_days]

        if not filtered_plans:
            return None

        # 如果没有指定权重，使用默认权重
        # 注意：权重配置要确保推荐的方案是综合考虑的，而不是极端偏向某一个维度
        if weights is None:
            if priority == "time":
                # 时效优先：时效权重较高，但也要考虑成本和服务
                weights = ScoringWeights(cost_weight=0.3, time_weight=0.5, service_weight=0.2)
            elif priority == "cost":
                # 成本优先：成本权重较高，但也要考虑时效和服务
                weights = ScoringWeights(cost_weight=0.5, time_weight=0.3, service_weight=0.2)
            else:
                # 均衡模式：综合考虑成本、时效、服务
                weights = ScoringWeights(cost_weight=0.4, time_weight=0.3, service_weight=0.3)

        # 计算每个方案的评分
        for plan in filtered_plans:
            score, details = self.calculate_score(plan, filtered_plans, weights)
            plan.score = score
            plan.score_details = details

        # 按评分降序排序（分数越高越好）
        sorted_plans = sorted(filtered_plans, key=lambda x: x.score if x.score else 0, reverse=True)
        best_plan = sorted_plans[0]

        # 生成推荐理由
        reason = self._generate_enhanced_reason(best_plan, plans, filtered_plans, max_days, weights)

        return Recommendation(plan=best_plan, reason=reason, rank=1)

    def _generate_reason(self, best: CarrierPlan, all_plans: List[CarrierPlan],
                         filtered_plans: List[CarrierPlan], max_days: Optional[int], priority: Optional[str] = None) -> str:
        """生成推荐理由（基础版）"""
        reasons = []

        # 根据优先级显示不同的推荐理由
        if priority == "time":
            reasons.append(f"时间最优：{best.transport_days}天，是最快的方案")
            reasons.append(f"成本：${best.total_cost:.2f}")
        else:
            avg_cost = sum(p.total_cost for p in all_plans) / len(all_plans)
            savings = avg_cost - best.total_cost
            savings_pct = (savings / avg_cost) * 100

            if savings > 0:
                reasons.append(f"成本最优：${best.total_cost:.2f}，比平均水平低${savings:.2f}({savings_pct:.1f}%)")

        if max_days:
            reasons.append(f"满足时效要求：{best.transport_days}天 <= {max_days}天")
        else:
            reasons.append(f"预计运输时间：{best.transport_days}天")

        mode_cn = "空运" if best.mode == "AIR" else "陆运"
        reasons.append(f"运输方式：{mode_cn}")

        service_cn = "门到门" if best.service_level == "DTD" else "门到港"
        reasons.append(f"服务级别：{service_cn}")

        if max_days is not None and len(filtered_plans) < len(all_plans):
            reasons.append(f"时效过滤：从{len(all_plans)}个方案中筛选出{len(filtered_plans)}个满足要求")

        return "；".join(reasons)

    def _generate_enhanced_reason(self, best: CarrierPlan, all_plans: List[CarrierPlan],
                                 filtered_plans: List[CarrierPlan], max_days: Optional[int],
                                 weights: ScoringWeights) -> str:
        """生成增强版推荐理由 - 包含评分详情"""
        reasons = []

        # 总体评分
        if best.score is not None:
            reasons.append(f"综合评分：{best.score:.3f}/1.0（加权算法）")

        # 各维度得分
        if best.score_details:
            details = best.score_details
            reasons.append(f"成本得分：{details['cost_score']:.3f}（权重{weights.cost_weight:.0%}）")
            reasons.append(f"时效得分：{details['time_score']:.3f}（权重{weights.time_weight:.0%}）")
            reasons.append(f"服务得分：{details['service_score']:.3f}（权重{weights.service_weight:.0%}）")

        # 具体信息
        reasons.append(f"总成本：${best.total_cost:.2f}")
        reasons.append(f"运输时间：{best.transport_days}天")
        reasons.append(f"服务评级：{best.service_rating or '未评级'}")

        mode_cn = "空运" if best.mode == "AIR" else "陆运"
        reasons.append(f"运输方式：{mode_cn}")

        service_cn = "门到门" if best.service_level == "DTD" else "门到港"
        reasons.append(f"服务级别：{service_cn}")

        if max_days is not None and len(filtered_plans) < len(all_plans):
            reasons.append(f"时效过滤：从{len(all_plans)}个方案中筛选出{len(filtered_plans)}个满足要求")

        return "；".join(reasons)

    def compare(self, order: OrderRequest) -> ComparisonResult:
        """执行比价 - 支持多维度评分"""
        plans = self.match_plans(order)

        # 确定使用的权重
        # 注意：权重配置要确保推荐的方案是综合考虑的，而不是极端偏向某一个维度
        if order.weights:
            weights = order.weights
        elif order.priority == "time":
            # 时效优先：时效权重较高，但也要考虑成本和服务
            weights = ScoringWeights(cost_weight=0.3, time_weight=0.5, service_weight=0.2)
        elif order.priority == "cost":
            # 成本优先：成本权重较高，但也要考虑时效和服务
            weights = ScoringWeights(cost_weight=0.5, time_weight=0.3, service_weight=0.2)
        else:
            # 均衡模式：综合考虑成本、时效、服务
            weights = ScoringWeights(cost_weight=0.4, time_weight=0.3, service_weight=0.3)

        recommendation = self.recommend_plan(plans, order.max_days, order.priority, weights)

        return ComparisonResult(
            order_info=order,
            available_plans=plans,
            recommended_plan=recommendation,
            total_plans_found=len(plans),
            filtered_by_time=order.max_days is not None,
            scoring_weights={
                'cost_weight': weights.cost_weight,
                'time_weight': weights.time_weight,
                'service_weight': weights.service_weight
            }
        )
