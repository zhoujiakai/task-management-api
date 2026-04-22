"""API v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1.tasks import router as tasks_router

router = APIRouter()
router.include_router(tasks_router)
