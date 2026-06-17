"""数据库初始化脚本 - 创建表并导入CSV数据

支持:
- 自动选择最优 CSV 数据源 (combined > with_rating > base)
- 批量导入 (每 1000 条提交一次)
- --reset 参数重建数据库
- 导入后一致性校验
"""
import os
import sys
import time
import argparse
import logging
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

import config
from database import init_database, get_session_factory, DB_PATH
from db_models import FreightRate
from common.data_cleaner import clean_dataframe

logger = logging.getLogger(__name__)


def _select_csv_path() -> str:
    """选择 CSV 数据源，优先级: combined > with_rating > base"""
    data_dir = config.CSV_DATA_DIR
    candidates = [
        os.path.join(data_dir, "FreightRates_combined.csv"),
        os.path.join(data_dir, "FreightRates_with_rating.csv"),
        os.path.join(data_dir, "FreightRates.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"未找到 CSV 数据文件，目录: {data_dir}")


def _load_and_clean_csv(csv_path: str) -> pd.DataFrame:
    """加载并清洗 CSV 数据"""
    logger.info(f"正在读取 CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    # 如果主文件不是 combined，尝试合并 extended 数据
    extended_path = os.path.join(config.CSV_DATA_DIR, "FreightRates_extended.csv")
    if csv_path != extended_path and os.path.exists(extended_path):
        extended_df = pd.read_csv(extended_path)
        df = pd.concat([df, extended_df], ignore_index=True)
        df = df.drop_duplicates()
        logger.info(f"已合并扩展数据，总行数: {len(df)}")

    df = clean_dataframe(df)
    logger.info(f"清洗后有效记录: {len(df)} 条")
    return df


def import_csv_to_db(csv_path: str = None):
    """从CSV文件导入数据到数据库"""
    if csv_path is None:
        csv_path = _select_csv_path()

    df = _load_and_clean_csv(csv_path)

    Session = get_session_factory()
    session = Session()
    start_time = time.time()

    try:
        # 清空现有数据
        session.query(FreightRate).delete()
        session.commit()

        # 构造记录字典列表
        records = []
        for _, row in df.iterrows():
            records.append({
                "carrier": row['Carrier'],
                "orig_port": row['Orig_Port'],
                "dest_port": row['Dest_Port'],
                "min_weight": float(row['Min_Weight_Quant']),
                "max_weight": float(row['Max_Weight_Quant']),
                "service_level": row['Service_Level'],
                "min_cost": float(row['Min_Cost']),
                "rate": float(row['Rate']),
                "mode": row['Mode_DSC'],
                "transport_days": int(row['TPT_Day_Count']),
                "carrier_type": row['Carrier_Type'],
                "service_rating": row.get('Service_Rating', 'C'),
            })

        # 批量插入
        batch_size = config.IMPORT_BATCH_SIZE
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            session.bulk_insert_mappings(FreightRate, batch)
            session.commit()
            logger.info(f"已导入 {min(i + batch_size, len(records))}/{len(records)} 条")

        elapsed = time.time() - start_time
        logger.info(f"导入完成: {len(records)} 条，耗时 {elapsed:.2f}s")

        # 一致性校验
        _validate_import(session, df)

    except Exception as e:
        session.rollback()
        logger.error(f"导入失败: {e}")
        raise
    finally:
        session.close()


def _validate_import(session, csv_df: pd.DataFrame):
    """导入后一致性校验"""
    from sqlalchemy import func, distinct

    db_count = session.query(func.count(FreightRate.id)).scalar()
    csv_count = len(csv_df)

    if db_count != csv_count:
        logger.error(f"行数不一致: DB={db_count}, CSV={csv_count}")
        raise RuntimeError(f"数据校验失败: DB 行数 {db_count} != CSV 行数 {csv_count}")

    # 检查关键统计
    db_carriers = session.query(func.count(distinct(FreightRate.carrier))).scalar()
    csv_carriers = csv_df['Carrier'].nunique()
    if db_carriers != csv_carriers:
        logger.error(f"承运商数不一致: DB={db_carriers}, CSV={csv_carriers}")
        raise RuntimeError(f"数据校验失败: 承运商数不一致")

    logger.info(f"数据校验通过: {db_count} 条记录, {db_carriers} 家承运商")


def main():
    """主函数，支持命令行参数"""
    parser = argparse.ArgumentParser(description="SQLite 数据库初始化")
    parser.add_argument("--reset", action="store_true", help="重建数据库（删除旧文件）")
    parser.add_argument("--csv", type=str, help="指定 CSV 文件路径")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=" * 50)
    print("SQLite 数据库初始化")
    print("=" * 50)

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"已删除旧数据库: {DB_PATH}")

    print("\n正在创建数据库表...")
    engine = init_database()
    print(f"数据库: {engine.url}")

    try:
        import_csv_to_db(args.csv)
        print("\n初始化完成!")
    except Exception as e:
        print(f"\n初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
