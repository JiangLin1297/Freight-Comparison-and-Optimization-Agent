"""集中配置管理 - 支持环境变量和 .env 文件覆盖"""
import os

# 加载 .env 文件
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# 数据源类型: csv | sqlite (默认 sqlite)
DATA_STORE = os.environ.get("DATA_STORE", "sqlite").lower()

# SQLite 数据库路径
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "freight.db"))

# CSV 数据目录
CSV_DATA_DIR = os.environ.get("CSV_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))

# 缓存 TTL (秒)
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))

# 数据完整性检查的最低行数
EXPECTED_MIN_ROW_COUNT = int(os.environ.get("EXPECTED_MIN_ROW_COUNT", "9000"))

# 批量导入每批次大小
IMPORT_BATCH_SIZE = int(os.environ.get("IMPORT_BATCH_SIZE", "1000"))

# 数据库锁重试次数和间隔
DB_RETRY_COUNT = int(os.environ.get("DB_RETRY_COUNT", "3"))
DB_RETRY_INTERVAL = float(os.environ.get("DB_RETRY_INTERVAL", "0.1"))
