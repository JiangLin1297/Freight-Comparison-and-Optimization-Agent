"""数据库连接模块 - 使用SQLite本地数据库"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# SQLite数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "freight.db")


def get_database_url() -> str:
    """构建SQLite数据库连接URL"""
    return f"sqlite:///{DB_PATH}"


def create_db_engine():
    """创建数据库引擎"""
    url = get_database_url()
    return create_engine(url, echo=False, connect_args={"check_same_thread": False})


# 全局变量，延迟初始化
_engine = None
_SessionLocal = None


def get_engine():
    """获取或创建数据库引擎"""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory():
    """获取或创建会话工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def get_db():
    """获取数据库会话（用于依赖注入）"""
    Session = get_session_factory()
    db = Session()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库（创建表）"""
    from db_models import FreightRate  # noqa: F401
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine
