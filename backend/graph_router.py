"""
转运路径搜索模块 - 当无直达路线时查找多跳转运路径

算法: BFS 最短跳数搜索, 每跳需满足重量约束
防环: visited 集合保证不重复访问, 无需额外跳数限制
"""
from collections import deque
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class RouteNode:
    """BFS 路径节点"""
    port: str
    path: List[str] = field(default_factory=list)


@dataclass
class TransferRoute:
    """转运路线方案"""
    path: List[str]                        # 港口序列
    legs: List[List[Dict]]                 # 每段的可选方案列表
    total_min_cost: float = 0.0            # 各段最低成本之和
    total_min_days: int = 0                # 各段最短天数之和 (不含转运)
    hop_count: int = 0                     # 转运次数
    transfer_penalty_days: int = 1         # 每次转运额外天数
    total_estimated_days: int = 0          # 含转运的总天数
    is_direct: bool = False
    # 评分相关
    score: Optional[float] = None          # 综合评分 (由 FreightService 填充)
    score_details: Optional[Dict] = None   # 评分明细
    best_leg_carriers: List[str] = field(default_factory=list)  # 各段最优承运商
    best_leg_modes: List[str] = field(default_factory=list)
    avg_service_rating: str = "C"          # 各段服务评级均值

    def __post_init__(self):
        if self.legs:
            bests = []
            self.total_min_cost = 0.0
            self.total_min_days = 0
            for leg in self.legs:
                if leg:
                    best = min(leg, key=lambda x: x['total_cost'])
                    bests.append(best)
                    self.total_min_cost += best['total_cost']
                    self.total_min_days += best['transport_days']
            self.hop_count = len(self.legs) - 1
            self.total_estimated_days = (
                self.total_min_days +
                self.hop_count * self.transfer_penalty_days
            )
            self.best_leg_carriers = [b['carrier'] for b in bests]
            self.best_leg_modes = [b['mode'] for b in bests]
            # 服务评级取最低 (木桶效应: 最差的一段决定整体体验)
            all_ratings = [b.get('service_rating', 'C') for b in bests]
            rating_order = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
            self.avg_service_rating = min(all_ratings, key=lambda r: rating_order.get(r, 3))


@dataclass
class RoutingResult:
    """路由搜索结果"""
    direct_routes: List[TransferRoute] = field(default_factory=list)
    transfer_routes: List[TransferRoute] = field(default_factory=list)
    # 次优推荐 (所有路径都不可行时)
    fallback_route: Optional[TransferRoute] = None
    fallback_reason: str = ""


class GraphRouter:
    """运输路线图路由器 - BFS 搜索转运路径, 不限跳数"""

    def __init__(self, data_store):
        self.store = data_store
        self._adj = None
        self._ports = None

    def _build_adjacency(self, weight: float) -> Dict[str, List[str]]:
        """根据货物重量构建邻接表"""
        df = self.store.df
        if df.empty or 'Min_Weight_Quant' not in df.columns:
            return {}
        valid = df[(df['Min_Weight_Quant'] <= weight) &
                    (df['Max_Weight_Quant'] >= weight)]
        adj = {}
        for orig, group in valid.groupby('Orig_Port'):
            adj[orig] = sorted(group['Dest_Port'].unique().tolist())
        all_ports = sorted(set(df['Orig_Port'].unique()) |
                           set(df['Dest_Port'].unique()))
        for p in all_ports:
            if p not in adj:
                adj[p] = []
        self._adj = adj
        self._ports = all_ports
        return adj

    def _bfs_shortest_path(self, orig: str, dest: str,
                           adj: Dict[str, List[str]]) -> Optional[List[str]]:
        """
        BFS 查找最短跳数路径。
        visited 集合保证不重复访问, 自然防环, 无需人工跳数限制。
        """
        if orig == dest:
            return [orig]
        if orig not in adj:
            return None

        visited = {orig}
        queue = deque([RouteNode(port=orig, path=[orig])])

        while queue:
            node = queue.popleft()
            for neighbor in adj.get(node.port, []):
                if neighbor == dest:
                    return node.path + [dest]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(RouteNode(
                        port=neighbor,
                        path=node.path + [neighbor]
                    ))

        return None

    def _get_leg_plans(self, from_port: str, to_port: str,
                       weight: float) -> List[Dict]:
        """获取某一段的所有可行方案"""
        df = self.store.df
        mask = (
            (df['Orig_Port'] == from_port) &
            (df['Dest_Port'] == to_port) &
            (df['Min_Weight_Quant'] <= weight) &
            (df['Max_Weight_Quant'] >= weight)
        )
        matched = df[mask]
        if matched.empty:
            return []

        results = []
        for _, row in matched.iterrows():
            total_cost = max(row['Min_Cost'], row['Rate'] * weight)
            results.append({
                "carrier": row['Carrier'],
                "orig_port": row['Orig_Port'],
                "dest_port": row['Dest_Port'],
                "min_weight": row['Min_Weight_Quant'],
                "max_weight": row['Max_Weight_Quant'],
                "service_level": row['Service_Level'],
                "min_cost": round(row['Min_Cost'], 2),
                "rate": round(row['Rate'], 4),
                "mode": row['Mode_DSC'].strip(),
                "transport_days": int(row['TPT_Day_Count']),
                "carrier_type": row['Carrier_Type'],
                "service_rating": row.get('Service_Rating', 'C'),
                "total_cost": round(total_cost, 2),
                "cost_formula": (
                    f"max({row['Min_Cost']:.2f}, {row['Rate']:.4f} * {weight})"
                    f" = {total_cost:.2f}"
                ),
                "is_exact_match": True
            })
        return results

    def _path_to_route(self, path: List[str], weight: float,
                       max_days: Optional[int] = None) -> Optional[TransferRoute]:
        """将路径转换为 TransferRoute (含各段方案验证)"""
        legs = []
        for i in range(len(path) - 1):
            leg_plans = self._get_leg_plans(path[i], path[i + 1], weight)
            if not leg_plans:
                return None
            legs.append(leg_plans)

        route = TransferRoute(
            path=path,
            legs=legs,
            is_direct=(len(path) == 2)
        )

        if max_days is not None and route.total_estimated_days > max_days:
            return None
        return route

    def find_routes(self, orig: str, dest: str, weight: float,
                    max_days: Optional[int] = None) -> RoutingResult:
        """
        查找从 orig 到 dest 的所有可行路线。

        策略:
        1. 直达存在且满足时效 → 返回直达
        2. 直达不满足 → BFS 搜转运 → 返回满足条件的转运
        3. 都找不到 → 返回 fallback (最快的转运/直达, 即使不满足时效)
        """
        adj = self._build_adjacency(weight)
        result = RoutingResult()

        if orig == dest:
            return result

        # ── 1. 直达 ──
        if dest in adj.get(orig, []):
            route = self._path_to_route([orig, dest], weight, max_days)
            if route:
                result.direct_routes.append(route)
                # 直达满足时效 → 直接返回
                return result

        # ── 2. 直达不满足时效或无直达 → BFS 转运 ──
        if not result.direct_routes:
            path = self._bfs_shortest_path(orig, dest, adj)
            if path and len(path) > 2:
                route = self._path_to_route(path, weight, max_days)
                if route:
                    result.transfer_routes.append(route)

        # ── 3. 最短路径不满足时效 → DFS 搜索所有路径找满足条件的 ──
        if not result.direct_routes and not result.transfer_routes and max_days is not None:
            all_paths = self._find_all_paths(orig, dest, adj)
            for path in all_paths:
                if len(path) <= 2:
                    continue
                route = self._path_to_route(path, weight, max_days)
                if route:
                    result.transfer_routes.append(route)

        # ── 4. 按总天数排序 ──
        result.transfer_routes.sort(
            key=lambda r: (r.total_estimated_days, r.total_min_cost)
        )

        # ── 5. 次优推荐 (所有可行路径都不满足条件) ──
        if not result.direct_routes and not result.transfer_routes:
            # 找一个"最接近"的方案作为提示
            fallback = self._find_best_effort(orig, dest, weight, adj)
            if fallback:
                result.fallback_route = fallback
                if max_days is not None:
                    result.fallback_reason = (
                        f"在 {max_days} 天时效内没有可用方案。"
                        f"最快可选方案需要 {fallback.total_estimated_days} 天"
                        f"{' (含' + str(fallback.hop_count) + '次转运)' if fallback.hop_count > 0 else ''}。"
                        f"建议放宽时效要求。"
                    )
                else:
                    result.fallback_reason = (
                        "未找到完全满足条件的方案，以下为最接近的方案。"
                    )

        return result

    def _find_best_effort(self, orig: str, dest: str, weight: float,
                          adj: Dict[str, List[str]]) -> Optional[TransferRoute]:
        """
        找到"最接近"的方案 (忽略时效约束):
        1. 如果直达存在但超时 → 返回直达
        2. 否则 BFS 最短路径 → 返回转运
        3. 都没有 → None
        """
        # 直达是否存在?
        if dest in adj.get(orig, []):
            return self._path_to_route([orig, dest], weight, max_days=None)

        # BFS 找最短转运
        path = self._bfs_shortest_path(orig, dest, adj)
        if path and len(path) > 2:
            return self._path_to_route(path, weight, max_days=None)

        return None

    def _find_all_paths(self, orig: str, dest: str,
                        adj: Dict[str, List[str]]) -> List[List[str]]:
        """
        DFS 查找所有路径 (无跳数限制, visited 防环)。
        按路径长度排序返回。
        """
        results = []

        def dfs(current: str, path: List[str], visited: set):
            if current == dest and len(path) > 1:
                results.append(list(path))
                return
            for neighbor in adj.get(current, []):
                if neighbor not in visited or neighbor == dest:
                    dfs(neighbor, path + [neighbor],
                        visited | {neighbor})

        dfs(orig, [orig], {orig})
        results.sort(key=len)
        return results

    def format_route_display(self, route: TransferRoute) -> str:
        """格式化路线为展示文本"""
        if route.is_direct:
            return f"直达: {' → '.join(route.path)}"

        parts = []
        for i, leg in enumerate(route.legs):
            from_p = route.path[i]
            to_p = route.path[i + 1]
            best = min(leg, key=lambda x: x['total_cost'])
            parts.append(
                f"第{i+1}段 {from_p}→{to_p}: "
                f"{best['carrier']} {best['mode']} "
                f"${best['total_cost']:.2f} / {best['transport_days']}天"
            )

        summary = (
            f"转运路线 ({route.hop_count}次转运): "
            f"总成本约 ${route.total_min_cost:.2f}, "
            f"预计总耗时 {route.total_estimated_days}天 "
            f"(运输{route.total_min_days}天 + 转运{route.hop_count}天)"
        )
        return "\n".join([summary] + parts)


def build_router(data_store) -> GraphRouter:
    """创建路由器实例"""
    return GraphRouter(data_store)
