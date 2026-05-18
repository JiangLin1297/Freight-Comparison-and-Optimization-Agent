"""运费比价服务 - 使用CSV数据源"""
import pandas as pd
from typing import List, Optional, Dict, Any
from models import OrderRequest, CarrierPlan, ComparisonResult, Recommendation


class CSVDataStore:
    """CSV文件数据源"""

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
                cost_formula=f"max({row['min_cost']:.2f}, {row['rate']:.4f} * {order.weight}) = {total_cost:.2f}"
            )
            plans.append(plan)
        return plans

    def recommend_plan(self, plans: List[CarrierPlan], max_days: Optional[int] = None) -> Optional[Recommendation]:
        """推荐最优方案"""
        if not plans:
            return None

        filtered_plans = plans
        if max_days is not None:
            filtered_plans = [p for p in plans if p.transport_days <= max_days]

        if not filtered_plans:
            return None

        sorted_plans = sorted(filtered_plans, key=lambda x: x.total_cost)
        best_plan = sorted_plans[0]
        reason = self._generate_reason(best_plan, plans, filtered_plans, max_days)

        return Recommendation(plan=best_plan, reason=reason, rank=1)

    def _generate_reason(self, best: CarrierPlan, all_plans: List[CarrierPlan],
                         filtered_plans: List[CarrierPlan], max_days: Optional[int]) -> str:
        """生成推荐理由"""
        reasons = []
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

    def compare(self, order: OrderRequest) -> ComparisonResult:
        """执行比价"""
        plans = self.match_plans(order)
        recommendation = self.recommend_plan(plans, order.max_days)
        return ComparisonResult(
            order_info=order,
            available_plans=plans,
            recommended_plan=recommendation,
            total_plans_found=len(plans),
            filtered_by_time=order.max_days is not None
        )
