"""CSVDataStore vs DBDataStore 一致性测试

验证两种数据源在相同输入下返回相同结果。
运行方式: cd backend && python -m pytest ../tests/test_store_consistency.py -v
"""
import os
import sys
import random

# 将 backend 目录加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models import OrderRequest


def _get_csv_store():
    """创建 CSVDataStore 实例"""
    from freight_service import CSVDataStore
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    candidates = [
        os.path.join(data_dir, "FreightRates_combined.csv"),
        os.path.join(data_dir, "FreightRates_with_rating.csv"),
        os.path.join(data_dir, "FreightRates.csv"),
    ]
    csv_path = next((p for p in candidates if os.path.exists(p)), None)
    assert csv_path, f"未找到 CSV 文件: {data_dir}"
    extended = os.path.join(data_dir, "FreightRates_extended.csv")
    return CSVDataStore(csv_path, extended if csv_path != extended else None)


def _get_db_store():
    """创建 DBDataStore 实例（自动建库）"""
    from freight_service import DBDataStore
    from database import init_db_if_needed
    init_db_if_needed()
    return DBDataStore()


def test_ports_consistency():
    """港口列表一致性"""
    csv = _get_csv_store()
    db = _get_db_store()

    csv_ports = csv.get_available_ports()
    db_ports = db.get_available_ports()

    assert csv_ports["orig_ports"] == db_ports["orig_ports"], \
        f"起运港不一致: CSV={len(csv_ports['orig_ports'])}, DB={len(db_ports['orig_ports'])}"
    assert csv_ports["dest_ports"] == db_ports["dest_ports"], \
        f"目的港不一致: CSV={len(csv_ports['dest_ports'])}, DB={len(db_ports['dest_ports'])}"
    print(f"港口一致性通过: {len(csv_ports['orig_ports'])} 起运港, {len(csv_ports['dest_ports'])} 目的港")


def test_statistics_consistency():
    """统计信息一致性"""
    csv = _get_csv_store()
    db = _get_db_store()

    csv_stats = csv.get_statistics()
    db_stats = db.get_statistics()

    assert csv_stats["total_records"] == db_stats["total_records"], \
        f"总记录数不一致: CSV={csv_stats['total_records']}, DB={db_stats['total_records']}"
    assert csv_stats["carriers"] == db_stats["carriers"], "承运商列表不一致"
    assert csv_stats["orig_ports"] == db_stats["orig_ports"], "起运港列表不一致"
    assert csv_stats["dest_ports"] == db_stats["dest_ports"], "目的港列表不一致"
    print(f"统计一致性通过: {csv_stats['total_records']} 条记录, {len(csv_stats['carriers'])} 家承运商")


def test_match_plans_consistency():
    """匹配方案一致性（随机 20 组）"""
    csv = _get_csv_store()
    db = _get_db_store()

    # 获取可用港口
    ports = csv.get_available_ports()
    orig_ports = ports["orig_ports"]
    dest_ports = ports["dest_ports"]

    # 随机生成 20 组测试用例
    random.seed(42)
    test_cases = []
    for _ in range(20):
        orig = random.choice(orig_ports)
        dest = random.choice(dest_ports)
        weight = random.uniform(10, 5000)
        test_cases.append((orig, dest, weight))

    mismatches = []
    for orig, dest, weight in test_cases:
        order = OrderRequest(weight=weight, orig_port=orig, dest_port=dest)
        def _plan_sort_key(p):
            return (p['carrier'], p.get('service_level', ''), p.get('mode', ''),
                    round(p.get('min_weight', 0), 3), round(p.get('max_weight', 0), 3),
                    round(p.get('min_cost', 0), 2), round(p.get('rate', 0), 4))
        csv_plans = sorted(csv.match_plans(order), key=_plan_sort_key)
        db_plans = sorted(db.match_plans(order), key=_plan_sort_key)

        # 比较数量
        if len(csv_plans) != len(db_plans):
            mismatches.append(
                f"[{orig}->{dest} w={weight:.1f}] 数量不同: CSV={len(csv_plans)}, DB={len(db_plans)}"
            )
            continue

        # 比较每个方案的关键字段
        for i, (cp, dp) in enumerate(zip(csv_plans, db_plans)):
            for key in ["carrier", "orig_port", "dest_port", "service_level", "mode",
                        "carrier_type", "service_rating", "is_exact_match"]:
                if cp.get(key) != dp.get(key):
                    mismatches.append(
                        f"[{orig}->{dest} w={weight:.1f}] plan[{i}].{key}: "
                        f"CSV={cp.get(key)}, DB={dp.get(key)}"
                    )
            # 数值字段允许小误差
            for key in ["min_weight", "max_weight", "min_cost", "rate"]:
                cv, dv = cp.get(key, 0), dp.get(key, 0)
                if abs(cv - dv) > 0.01:
                    mismatches.append(
                        f"[{orig}->{dest} w={weight:.1f}] plan[{i}].{key}: "
                        f"CSV={cv}, DB={dv} (差异 > 0.01)"
                    )

    if mismatches:
        print("发现不一致:")
        for m in mismatches:
            print(f"  - {m}")
        assert False, f"共 {len(mismatches)} 处不一致"
    else:
        print(f"匹配一致性通过: 20 组测试用例全部一致")


def test_count_matching_consistency():
    """count_matching 一致性（随机 20 组）"""
    csv = _get_csv_store()
    db = _get_db_store()

    ports = csv.get_available_ports()
    orig_ports = ports["orig_ports"]
    dest_ports = ports["dest_ports"]

    random.seed(123)
    mismatches = []
    for _ in range(20):
        orig = random.choice(orig_ports)
        dest = random.choice(dest_ports)
        weight = random.uniform(10, 5000)

        csv_count = csv.count_matching(weight, orig, dest)
        db_count = db.count_matching(weight, orig, dest)

        if csv_count != db_count:
            mismatches.append(
                f"[{orig}->{dest} w={weight:.1f}] CSV={csv_count}, DB={db_count}"
            )

    if mismatches:
        print("count_matching 不一致:")
        for m in mismatches:
            print(f"  - {m}")
        assert False, f"共 {len(mismatches)} 处不一致"
    else:
        print("count_matching 一致性通过: 20 组测试用例全部一致")


if __name__ == "__main__":
    print("=" * 50)
    print("CSV vs DB 一致性测试")
    print("=" * 50)
    print()

    try:
        test_ports_consistency()
        test_statistics_consistency()
        test_match_plans_consistency()
        test_count_matching_consistency()
        print("\n全部测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
