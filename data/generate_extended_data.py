#!/usr/bin/env python3
"""
扩展费率数据生成脚本
生成更多目的港和承运商的费率数据，扩展系统覆盖范围
"""
import pandas as pd
import numpy as np
import random
import os

def generate_extended_data():
    """生成扩展的费率数据"""

    # 读取原始数据
    original_path = os.path.join(os.path.dirname(__file__), 'FreightRates_with_rating.csv')
    if not os.path.exists(original_path):
        original_path = os.path.join(os.path.dirname(__file__), 'FreightRates.csv')

    df = pd.read_csv(original_path)
    df.columns = df.columns.str.strip()

    print(f"原始数据: {len(df)} 条记录")
    print(f"原始起运港: {sorted(df['Orig_Port'].unique())}")
    print(f"原始目的港: {sorted(df['Dest_Port'].unique())}")
    print(f"原始承运商: {sorted(df['Carrier'].unique())}")

    # 定义新的港口（增加更多目的港）
    new_dest_ports = ['PORT01', 'PORT02', 'PORT03', 'PORT04', 'PORT05', 'PORT06', 'PORT07']

    # 定义新的承运商
    new_carriers = ['V555_0', 'V555_1', 'V666_0', 'V666_1', 'V777_0']

    # 评级分布权重
    rating_weights = {'A': 0.15, 'B': 0.25, 'C': 0.35, 'D': 0.15, 'E': 0.10}

    new_records = []

    # 为每个原始记录生成到新港口的记录
    for _, row in df.iterrows():
        for new_port in new_dest_ports:
            # 随机决定是否生成这条记录（控制数据量）
            if random.random() > 0.7:  # 30% 的概率生成
                continue

            new_row = row.copy()
            new_row['Dest_Port'] = new_port

            # 根据港口距离调整费率（模拟不同距离）
            distance_factors = {
                'PORT01': 1.3,  # 较远
                'PORT02': 1.2,
                'PORT03': 1.1,
                'PORT04': 1.0,  # 中等
                'PORT05': 0.9,
                'PORT06': 0.8,
                'PORT07': 0.7,  # 较近
            }
            distance_factor = distance_factors.get(new_port, 1.0)
            # 添加随机波动
            distance_factor *= random.uniform(0.85, 1.15)

            new_row['Rate'] = round(row['Rate'] * distance_factor, 4)
            new_row['Min_Cost'] = round(row['Min_Cost'] * distance_factor, 2)

            # 调整运输天数
            days_factor = distance_factor * random.uniform(0.9, 1.2)
            new_row['TPT_Day_Count'] = max(1, int(row['TPT_Day_Count'] * days_factor))

            # 随机分配评级
            if 'Service_Rating' in df.columns:
                ratings = list(rating_weights.keys())
                weights = list(rating_weights.values())
                new_row['Service_Rating'] = random.choices(ratings, weights=weights, k=1)[0]

            new_records.append(new_row)

    # 为新承运商生成数据
    for carrier in new_carriers:
        # 随机选择一些原始记录作为模板
        sample_size = min(50, len(df))
        sample_df = df.sample(n=sample_size)

        for _, row in sample_df.iterrows():
            # 为每个新承运商生成多条记录
            for _ in range(random.randint(1, 3)):
                new_row = row.copy()
                new_row['Carrier'] = carrier

                # 新承运商的费率略有不同
                rate_factor = random.uniform(0.8, 1.3)
                new_row['Rate'] = round(row['Rate'] * rate_factor, 4)
                new_row['Min_Cost'] = round(row['Min_Cost'] * rate_factor, 2)

                # 运输天数
                days_variation = random.randint(-2, 3)
                new_row['TPT_Day_Count'] = max(1, int(row['TPT_Day_Count']) + days_variation)

                # 承运商类型
                new_row['Carrier_Type'] = f"V{carrier.split('_')[0][1:]}_{random.randint(0, 2)}"

                # 随机分配评级
                if 'Service_Rating' in df.columns:
                    ratings = list(rating_weights.keys())
                    weights = list(rating_weights.values())
                    new_row['Service_Rating'] = random.choices(ratings, weights=weights, k=1)[0]

                new_records.append(new_row)

    # 合并数据
    new_df = pd.DataFrame(new_records)
    extended_df = pd.concat([df, new_df], ignore_index=True)

    # 去重
    extended_df = extended_df.drop_duplicates()

    # 保存
    output_path = os.path.join(os.path.dirname(__file__), 'FreightRates_extended.csv')
    extended_df.to_csv(output_path, index=False)

    print(f"\n扩展数据: {len(extended_df)} 条记录")
    print(f"扩展后起运港: {sorted(extended_df['Orig_Port'].unique())}")
    print(f"扩展后目的港: {sorted(extended_df['Dest_Port'].unique())}")
    print(f"扩展后承运商: {sorted(extended_df['Carrier'].unique())}")
    print(f"\n数据已保存到: {output_path}")

    return extended_df


def update_main_datastore():
    """更新主数据文件，合并原始数据和扩展数据"""
    original_path = os.path.join(os.path.dirname(__file__), 'FreightRates_with_rating.csv')
    extended_path = os.path.join(os.path.dirname(__file__), 'FreightRates_extended.csv')

    if not os.path.exists(extended_path):
        print("扩展数据文件不存在，请先运行 generate_extended_data()")
        return

    # 读取数据
    original_df = pd.read_csv(original_path)
    extended_df = pd.read_csv(extended_path)

    # 合并
    combined_df = pd.concat([original_df, extended_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates()

    # 保存为新的主数据文件
    combined_path = os.path.join(os.path.dirname(__file__), 'FreightRates_combined.csv')
    combined_df.to_csv(combined_path, index=False)

    print(f"合并数据: {len(combined_df)} 条记录")
    print(f"已保存到: {combined_path}")

    return combined_df


if __name__ == '__main__':
    print("=" * 60)
    print("扩展费率数据生成器")
    print("=" * 60)
    print()

    # 生成扩展数据
    extended_df = generate_extended_data()

    print()
    print("=" * 60)
    print("合并数据")
    print("=" * 60)
    print()

    # 合并数据
    combined_df = update_main_datastore()

    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)
