"""异步 SQLAlchemy 数据库引擎和会话管理。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import cfg

engine = create_async_engine(cfg.database.url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖，用于提供数据库会话。"""
    async with async_session() as session:
        yield session


async def create_tables() -> None:
    """创建所有数据库表。"""
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
