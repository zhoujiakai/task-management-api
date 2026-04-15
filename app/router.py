"""任务管理 API 的 CRUD 路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.cache import invalidate_cache, lookup, store_in_cache
from app.database import get_db
from app.exceptions import TaskNotFoundException
from app.models import Task, TaskStatus
from app.notifications import send_notification
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.weather import fetch_weather

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_api_key)])


def _serialize_task(task: Task, weather_info: str | None = None) -> dict:
    """将 ORM 对象序列化为可缓存的字典。"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "weather_info": weather_info,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """创建新任务，并尝试获取 due_date 当天的天气预报。"""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=TaskStatus(task_in.status),
        due_date=task_in.due_date,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    weather_info = await fetch_weather(task.due_date)
    cache_data = _serialize_task(task, weather_info)
    store_in_cache(task.id, cache_data)
    return cache_data


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    """列出所有任务，可按状态筛选，支持分页。"""
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == TaskStatus(status))
    stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """通过 ID 获取指定任务（带缓存），包含天气信息。"""
    # 先查缓存（缓存中可能包含天气数据）
    cached = lookup(task_id)
    if cached is not None:
        return cached

    # 缓存未命中，查数据库
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    # 获取天气信息
    weather_info = await fetch_weather(task.due_date)
    cache_data = _serialize_task(task, weather_info)
    store_in_cache(task.id, cache_data)
    return cache_data


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, task_in: TaskUpdate, db: AsyncSession = Depends(get_db)
) -> Task:
    """更新已有任务。"""
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    update_data = task_in.model_dump(exclude_unset=True)
    old_status = task.status

    if "status" in update_data:
        update_data["status"] = TaskStatus(update_data["status"])
    if "title" in update_data:
        task.title = update_data["title"]
    if "description" in update_data:
        task.description = update_data["description"]
    if "status" in update_data:
        task.status = update_data["status"]
    if "due_date" in update_data:
        task.due_date = update_data["due_date"]

    await db.commit()
    await db.refresh(task)

    # 更新缓存（重新获取天气）
    weather_info = await fetch_weather(task.due_date)
    store_in_cache(task.id, _serialize_task(task, weather_info))

    # 当任务被标记为已完成时触发通知
    if task.status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
        await send_notification(task.id, task.title, task.status.value)

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """删除任务。"""
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)
    await db.delete(task)
    await db.commit()
    invalidate_cache(task_id)
