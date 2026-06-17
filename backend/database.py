"""数据库连接模块 - 使用SQLite本地数据库

提供线程安全的会话管理、WAL 模式配置、健康检查和自动初始化。
"""
import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError

import config

logger = logging.getLogger(__name__)

Base = declarative_base()

# 数据库路径
DB_PATH = config.DB_PATH


def get_database_url() -> str:
    """构建SQLite数据库连接URL"""
    return f"sqlite:///{DB_PATH}"


def create_db_engine():
    """创建数据库引擎，配置 WAL 模式和连接参数"""
    url = get_database_url()
    engine = create_engine(
        url,
        echo=False,
        connect_args={
            "check_same_thread": False,
            "timeout": 10,
        },
        poolclass=StaticPool,
    )

    # 连接时执行 PRAGMA 优化
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    return engine


# 全局变量，延迟初始化
_engine = None
_session_factory = None
_scoped_session = None


def get_engine():
    """获取或创建数据库引擎"""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory():
    """获取或创建会话工厂"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory


def get_scoped_session():
    """获取线程安全的 scoped_session"""
    global _scoped_session
    if _scoped_session is None:
        _scoped_session = scoped_session(get_session_factory())
    return _scoped_session


def get_db():
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    Session = get_scoped_session()
    session = Session()
    try:
        yield session
    finally:
        session.close()


def get_session():
    """获取数据库会话（普通调用，需手动关闭）"""
    Session = get_scoped_session()
    return Session()


def execute_with_retry(func, *args, **kwargs):
    """执行数据库操作，遇到 lock 错误时重试"""
    import time
    last_error = None
    for attempt in range(config.DB_RETRY_COUNT):
        try:
            return func(*args, **kwargs)
        except OperationalError as e:
            if "locked" in str(e).lower():
                last_error = e
                logger.warning(f"数据库锁定，重试 {attempt + 1}/{config.DB_RETRY_COUNT}")
                time.sleep(config.DB_RETRY_INTERVAL)
            else:
                raise
    raise last_error


def init_database():
    """初始化数据库（创建表）"""
    from db_models import FreightRate  # noqa: F401
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def check_db_integrity(expected_row_count: int = None) -> bool:
    """
    数据库健康检查:
    1. 检查 db 文件是否存在且可读
    2. 执行 PRAGMA integrity_check
    3. 查询行数与预期比较
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return False

    try:
        engine = get_engine()
        with engine.connect() as conn:
            # integrity_check
            result = conn.execute(text("PRAGMA integrity_check")).scalar()
            if result != "ok":
                logger.error(f"数据库完整性检查失败: {result}")
                return False

            # 行数检查
            count = conn.execute(text("SELECT COUNT(*) FROM freight_rates")).scalar()
            if count == 0:
                logger.warning("数据库表为空")
                return False

            if expected_row_count is not None and count < expected_row_count:
                logger.error(f"数据行数不足: {count} < {expected_row_count}")
                return False

            logger.info(f"数据库健康检查通过: {count} 条记录")
            return True
    except Exception as e:
        logger.error(f"数据库健康检查异常: {e}")
        return False


def init_db_if_needed(force: bool = False) -> bool:
    """
    启动时自动初始化数据库:
    - force=True: 强制重新建库导入
    - 否则: 检查是否已有数据，无数据则导入
    返回 True 表示数据库就绪。
    """
    if force:
        # 清空表数据而非删除文件（避免 Windows 文件锁问题）
        init_database()
        try:
            from db_models import FreightRate
            session = get_session()
            try:
                session.query(FreightRate).delete()
                session.commit()
                logger.info("已清空表数据")
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"清空表失败: {e}")
    else:
        init_database()

    # 检查是否已有数据
    try:
        engine = get_engine()
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM freight_rates")).scalar()
            if count > 0:
                logger.info(f"数据库已有 {count} 条记录，跳过导入")
                return True
    except Exception:
        pass

    # 无数据，执行导入
    logger.info("数据库为空，开始从 CSV 导入数据...")
    try:
        from init_db import import_csv_to_db
        import_csv_to_db()
        return True
    except Exception as e:
        logger.error(f"数据导入失败: {e}")
        return False
