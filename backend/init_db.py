"""数据库初始化脚本 - 创建表并导入CSV数据"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database import init_database, get_session_factory
from db_models import FreightRate


def import_csv_to_db(csv_path: str):
    """从CSV文件导入数据到数据库"""
    print(f"正在读取CSV文件: {csv_path}")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # 清洗数据
    df['Mode_DSC'] = df['Mode_DSC'].str.strip()
    df['Min_Weight_Quant'] = pd.to_numeric(df['Min_Weight_Quant'], errors='coerce')
    df['Max_Weight_Quant'] = pd.to_numeric(df['Max_Weight_Quant'], errors='coerce')
    df['Min_Cost'] = pd.to_numeric(df['Min_Cost'], errors='coerce')
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')
    df['TPT_Day_Count'] = pd.to_numeric(df['TPT_Day_Count'], errors='coerce')

    # 删除包含NaN的行
    df = df.dropna()

    print(f"共 {len(df)} 条有效记录")

    # 获取会话
    Session = get_session_factory()
    session = Session()

    try:
        # 清空现有数据
        session.query(FreightRate).delete()
        session.commit()
        print("已清空现有数据")

        # 批量插入
        records = []
        for _, row in df.iterrows():
            record = FreightRate(
                carrier=row['Carrier'],
                orig_port=row['Orig_Port'],
                dest_port=row['Dest_Port'],
                min_weight=row['Min_Weight_Quant'],
                max_weight=row['Max_Weight_Quant'],
                service_level=row['Service_Level'],
                min_cost=row['Min_Cost'],
                rate=row['Rate'],
                mode=row['Mode_DSC'],
                transport_days=int(row['TPT_Day_Count']),
                carrier_type=row['Carrier_Type']
            )
            records.append(record)

        session.bulk_save_objects(records)
        session.commit()
        print(f"成功导入 {len(records)} 条记录到数据库")

    except Exception as e:
        session.rollback()
        print(f"导入失败: {e}")
        raise
    finally:
        session.close()


def main():
    """主函数"""
    print("=" * 50)
    print("SQLite 数据库初始化")
    print("=" * 50)

    # 创建表
    print("\n正在创建数据库表...")
    engine = init_database()
    print(f"数据库连接成功: {engine.url}")

    # 导入CSV数据
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "FreightRates.csv")
    if os.path.exists(csv_path):
        import_csv_to_db(csv_path)
    else:
        print(f"CSV文件不存在: {csv_path}")
        print("跳过数据导入")

    print("\n初始化完成!")


if __name__ == "__main__":
    main()
