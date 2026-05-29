#!/usr/bin/env python3
"""
测试评分功能的脚本
验证所有方案是否都有评分显示
"""
import requests
import json

def test_scoring():
    """测试评分功能"""
    print("=" * 60)
    print("测试评分功能")
    print("=" * 60)
    print()

    # 测试1: 均衡模式
    print("测试1: 均衡模式")
    print("-" * 40)
    response = requests.post('http://localhost:8000/api/compare', json={
        'weight': 100,
        'orig_port': 'PORT08',
        'dest_port': 'PORT09'
    })
    result = response.json()

    print(f"总方案数: {result['total_plans_found']}")
    print(f"评分权重: {result.get('scoring_weights', {})}")
    print()

    # 检查每个方案的评分
    all_have_scores = True
    for i, plan in enumerate(result['available_plans']):
        has_score = 'score' in plan and plan['score'] is not None
        has_details = 'score_details' in plan and plan['score_details'] is not None

        print(f"方案 {i+1}: {plan['carrier']}")
        print(f"  运输天数: {plan['transport_days']}天")
        print(f"  总成本: ${plan['total_cost']:.2f}")
        print(f"  服务评级: {plan.get('service_rating', 'N/A')}")
        print(f"  有评分: {'YES' if has_score else 'NO'}")
        if has_score:
            print(f"  综合评分: {plan['score']:.3f}")
        if has_details:
            print(f"  评分明细: 成本{plan['score_details']['cost_score']:.3f} + "
                  f"时效{plan['score_details']['time_score']:.3f} + "
                  f"服务{plan['score_details']['service_score']:.3f}")
        print()

        if not has_score:
            all_have_scores = False

    print("=" * 60)
    if all_have_scores:
        print("[OK] 所有方案都有评分！")
    else:
        print("[ERROR] 部分方案缺少评分！")
    print("=" * 60)
    print()

    # 测试2: 时效优先模式
    print("测试2: 时效优先模式")
    print("-" * 40)
    response = requests.post('http://localhost:8000/api/compare', json={
        'weight': 100,
        'orig_port': 'PORT08',
        'dest_port': 'PORT09',
        'priority': 'time'
    })
    result = response.json()

    print(f"评分权重: {result.get('scoring_weights', {})}")
    if result['recommended_plan']:
        plan = result['recommended_plan']['plan']
        print(f"推荐方案: {plan['carrier']}")
        print(f"运输天数: {plan['transport_days']}天")
        print(f"总成本: ${plan['total_cost']:.2f}")
        print(f"服务评级: {plan.get('service_rating', 'N/A')}")
        print(f"综合评分: {plan.get('score', 'N/A')}")
    print()

    # 测试3: 成本优先模式
    print("测试3: 成本优先模式")
    print("-" * 40)
    response = requests.post('http://localhost:8000/api/compare', json={
        'weight': 100,
        'orig_port': 'PORT08',
        'dest_port': 'PORT09',
        'priority': 'cost'
    })
    result = response.json()

    print(f"评分权重: {result.get('scoring_weights', {})}")
    if result['recommended_plan']:
        plan = result['recommended_plan']['plan']
        print(f"推荐方案: {plan['carrier']}")
        print(f"运输天数: {plan['transport_days']}天")
        print(f"总成本: ${plan['total_cost']:.2f}")
        print(f"服务评级: {plan.get('service_rating', 'N/A')}")
        print(f"综合评分: {plan.get('score', 'N/A')}")
    print()

if __name__ == '__main__':
    test_scoring()
