"""
测试运行器示例
用于演示如何使用 testdataset.csv 进行自动化测试
"""

import pandas as pd
import requests
import json
from typing import Dict, Any

# 配置
API_BASE_URL = "http://localhost:8000"
TEST_DATA_FILE = "testdataset.csv"
OUTPUT_FILE = "test_results.csv"


def load_test_data(file_path: str) -> pd.DataFrame:
    """加载测试数据"""
    return pd.read_csv(file_path)


def call_compare_api(weight: float, orig_port: str, dest_port: str,
                     max_days: int = None) -> Dict[str, Any]:
    """调用比价API"""
    payload = {
        "weight": weight,
        "orig_port": orig_port,
        "dest_port": dest_port
    }
    if max_days is not None:
        payload["max_days"] = max_days

    response = requests.post(f"{API_BASE_URL}/api/compare", json=payload)
    return response.json()


def validate_response(response: Dict[str, Any], test_case: pd.Series) -> Dict[str, Any]:
    """验证响应结果"""
    validation = {
        "test_id": test_case["test_id"],
        "status": "PASS",
        "errors": []
    }

    # 检查方案数量
    if pd.notna(test_case.get("expected_plans_count")):
        expected_count = int(test_case["expected_plans_count"])
        actual_count = response.get("total_plans_found", 0)
        if actual_count != expected_count:
            validation["errors"].append(
                f"方案数量不匹配: 预期={expected_count}, 实际={actual_count}"
            )

    # 检查推荐承运商
    if pd.notna(test_case.get("expected_recommend_carrier")):
        expected_carrier = test_case["expected_recommend_carrier"]
        actual_carrier = response.get("recommended_plan", {}).get("plan", {}).get("carrier")
        if actual_carrier != expected_carrier:
            validation["errors"].append(
                f"推荐承运商不匹配: 预期={expected_carrier}, 实际={actual_carrier}"
            )

    # 如果有错误，标记为失败
    if validation["errors"]:
        validation["status"] = "FAIL"

    return validation


def run_test(test_case: pd.Series) -> Dict[str, Any]:
    """运行单个测试用例"""
    test_id = test_case["test_id"]
    weight = test_case["weight"]
    orig_port = test_case["orig_port"]
    dest_port = test_case["dest_port"]
    max_days = test_case.get("max_days")

    print(f"运行测试 {test_id}: {test_case['description']}")

    try:
        # 调用API
        response = call_compare_api(weight, orig_port, dest_port, max_days)

        # 验证结果
        validation = validate_response(response, test_case)

        return {
            "test_id": test_id,
            "category": test_case["category"],
            "description": test_case["description"],
            "user_input": test_case["user_input"],
            "status": validation["status"],
            "errors": "; ".join(validation["errors"]) if validation["errors"] else "",
            "total_plans": response.get("total_plans_found", 0),
            "recommended_carrier": response.get("recommended_plan", {}).get("plan", {}).get("carrier", ""),
            "recommended_cost": response.get("recommended_plan", {}).get("plan", {}).get("total_cost", 0)
        }

    except Exception as e:
        return {
            "test_id": test_id,
            "category": test_case["category"],
            "description": test_case["description"],
            "user_input": test_case["user_input"],
            "status": "ERROR",
            "errors": str(e),
            "total_plans": 0,
            "recommended_carrier": "",
            "recommended_cost": 0
        }


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运输方案比价与优化智能体 - 测试运行器")
    print("=" * 60)

    # 加载测试数据
    test_data = load_test_data(TEST_DATA_FILE)
    print(f"\n加载了 {len(test_data)} 个测试用例")

    # 运行测试
    results = []
    for _, test_case in test_data.iterrows():
        result = run_test(test_case)
        results.append(result)
        print(f"  [{result['status']}] {result['test_id']}")

    # 统计结果
    results_df = pd.DataFrame(results)
    total = len(results_df)
    passed = len(results_df[results_df["status"] == "PASS"])
    failed = len(results_df[results_df["status"] == "FAIL"])
    errors = len(results_df[results_df["status"] == "ERROR"])

    print("\n" + "=" * 60)
    print("测试结果统计")
    print("=" * 60)
    print(f"总计: {total}")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    print(f"错误: {errors} ({errors/total*100:.1f}%)")

    # 保存结果
    results_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n详细结果已保存到: {OUTPUT_FILE}")

    # 显示失败的测试
    if failed > 0:
        print("\n失败的测试用例:")
        failed_tests = results_df[results_df["status"] == "FAIL"]
        for _, row in failed_tests.iterrows():
            print(f"  - {row['test_id']}: {row['errors']}")

    return results_df


def update_expected_results():
    """更新预期结果（首次运行时使用）"""
    print("更新预期结果...")

    test_data = load_test_data(TEST_DATA_FILE)

    for idx, test_case in test_data.iterrows():
        test_id = test_case["test_id"]
        weight = test_case["weight"]
        orig_port = test_case["orig_port"]
        dest_port = test_case["dest_port"]
        max_days = test_case.get("max_days")

        print(f"处理 {test_id}...")

        try:
            response = call_compare_api(weight, orig_port, dest_port, max_days)

            # 更新预期结果
            test_data.at[idx, "expected_plans_count"] = response.get("total_plans_found", 0)

            recommended = response.get("recommended_plan")
            if recommended:
                plan = recommended.get("plan", {})
                test_data.at[idx, "expected_recommend_carrier"] = plan.get("carrier", "")
                test_data.at[idx, "expected_cost_formula"] = plan.get("cost_formula", "")
                test_data.at[idx, "expected_min_cost"] = plan.get("min_cost", 0)

        except Exception as e:
            print(f"  错误: {e}")

    # 保存更新后的数据
    output_file = "testdataset_with_expected.csv"
    test_data.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n已保存更新后的测试数据到: {output_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        update_expected_results()
    else:
        run_all_tests()
