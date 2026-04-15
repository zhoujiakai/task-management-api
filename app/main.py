"""FastAPI 应用入口。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_tables
from app.exceptions import register_exception_handlers
from app.router import router
from config import cfg
from logger import create_logger

log = create_logger("app", cfg.logging.level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：启动时创建数据库表。"""
    log.info("Starting Task Management API")
    await create_tables()
    yield
    log.info("Shutting down Task Management API")


app = FastAPI(
    title="Task Management API",
    description="A RESTful API for managing tasks",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
