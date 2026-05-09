import pandas as pd
from typing import List, Optional
from models import OrderRequest, CarrierPlan, ComparisonResult, Recommendation


class FreightService:
    """运费比价服务"""

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()
        self._clean_data()

    def _clean_data(self):
        """清洗数据"""
        self.df['Mode_DSC'] = self.df['Mode_DSC'].str.strip()
        self.df['Min_Weight_Quant'] = pd.to_numeric(self.df['Min_Weight_Quant'], errors='coerce')
        self.df['Max_Weight_Quant'] = pd.to_numeric(self.df['Max_Weight_Quant'], errors='coerce')
        self.df['Min_Cost'] = pd.to_numeric(self.df['Min_Cost'], errors='coerce')
        self.df['Rate'] = pd.to_numeric(self.df['Rate'], errors='coerce')
        self.df['TPT_Day_Count'] = pd.to_numeric(self.df['TPT_Day_Count'], errors='coerce')

    def get_available_ports(self) -> dict:
        """获取可用港口列表"""
        orig_ports = sorted(self.df['Orig_Port'].unique().tolist())
        dest_ports = sorted(self.df['Dest_Port'].unique().tolist())
        return {
            "orig_ports": orig_ports,
            "dest_ports": dest_ports
        }

    def get_statistics(self) -> dict:
        """获取数据统计信息"""
        return {
            "total_records": len(self.df),
            "carriers": sorted(self.df['Carrier'].unique().tolist()),
            "orig_ports": sorted(self.df['Orig_Port'].unique().tolist()),
            "dest_ports": sorted(self.df['Dest_Port'].unique().tolist()),
            "transport_modes": sorted(self.df['Mode_DSC'].unique().tolist()),
            "service_levels": sorted(self.df['Service_Level'].unique().tolist()),
        }

    def calculate_cost(self, rate: float, min_cost: float, weight: float) -> float:
        """
        计算运输成本
        公式: Cost = max(Min_Cost, Rate * Weight)
        """
        calculated_cost = rate * weight
        return max(min_cost, calculated_cost)

    def match_plans(self, order: OrderRequest) -> List[CarrierPlan]:
        """
        匹配承运商方案
        筛选条件: 起运港匹配、目的港匹配、重量在区间内
        """
        df = self.df.copy()

        # 筛选匹配的方案
        mask = (
            (df['Orig_Port'] == order.orig_port) &
            (df['Dest_Port'] == order.dest_port) &
            (df['Min_Weight_Quant'] <= order.weight) &
            (df['Max_Weight_Quant'] >= order.weight)
        )

        matched = df[mask]

        plans = []
        for _, row in matched.iterrows():
            total_cost = self.calculate_cost(row['Rate'], row['Min_Cost'], order.weight)

            plan = CarrierPlan(
                carrier=row['Carrier'],
                orig_port=row['Orig_Port'],
                dest_port=row['Dest_Port'],
                min_weight=row['Min_Weight_Quant'],
                max_weight=row['Max_Weight_Quant'],
                service_level=row['Service_Level'],
                min_cost=round(row['Min_Cost'], 2),
                rate=round(row['Rate'], 4),
                mode=row['Mode_DSC'],
                transport_days=int(row['TPT_Day_Count']),
                carrier_type=row['Carrier_Type'],
                total_cost=round(total_cost, 2),
                cost_formula=f"max({row['Min_Cost']:.2f}, {row['Rate']:.4f} * {order.weight}) = {total_cost:.2f}"
            )
            plans.append(plan)

        return plans

    def recommend_plan(self, plans: List[CarrierPlan], max_days: Optional[int] = None) -> Optional[Recommendation]:
        """
        推荐最优方案
        规则: 在满足时效要求的方案中，选择成本最低的
        """
        if not plans:
            return None

        filtered_plans = plans
        filtered_by_time = False

        # 如果设置了最大运输天数，过滤不满足时效的方案
        if max_days is not None:
            filtered_plans = [p for p in plans if p.transport_days <= max_days]
            filtered_by_time = True

        if not filtered_plans:
            return None

        # 按成本排序，选择最低的
        sorted_plans = sorted(filtered_plans, key=lambda x: x.total_cost)
        best_plan = sorted_plans[0]

        reason = self._generate_reason(best_plan, plans, filtered_plans, max_days)

        return Recommendation(
            plan=best_plan,
            reason=reason,
            rank=1
        )

    def _generate_reason(self, best: CarrierPlan, all_plans: List[CarrierPlan],
                         filtered_plans: List[CarrierPlan], max_days: Optional[int]) -> str:
        """生成推荐理由"""
        reasons = []

        # 成本优势
        avg_cost = sum(p.total_cost for p in all_plans) / len(all_plans)
        savings = avg_cost - best.total_cost
        savings_pct = (savings / avg_cost) * 100

        if savings > 0:
            reasons.append(f"成本最优：${best.total_cost:.2f}，比平均水平低${savings:.2f}({savings_pct:.1f}%)")

        # 时效信息
        if max_days:
            reasons.append(f"满足时效要求：{best.transport_days}天 <= {max_days}天")
        else:
            reasons.append(f"预计运输时间：{best.transport_days}天")

        # 运输方式
        mode_cn = "空运" if best.mode == "AIR" else "陆运"
        reasons.append(f"运输方式：{mode_cn}")

        # 服务级别
        service_cn = "门到门" if best.service_level == "DTD" else "门到港"
        reasons.append(f"服务级别：{service_cn}")

        # 如果有时效过滤，说明过滤情况
        if max_days is not None and len(filtered_plans) < len(all_plans):
            reasons.append(f"时效过滤：从{len(all_plans)}个方案中筛选出{len(filtered_plans)}个满足要求")

        return "；".join(reasons)

    def compare(self, order: OrderRequest) -> ComparisonResult:
        """
        执行比价
        """
        plans = self.match_plans(order)
        recommendation = self.recommend_plan(plans, order.max_days)

        return ComparisonResult(
            order_info=order,
            available_plans=plans,
            recommended_plan=recommendation,
            total_plans_found=len(plans),
            filtered_by_time=order.max_days is not None
        )
