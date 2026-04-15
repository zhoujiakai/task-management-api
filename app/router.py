"""任务管理 API 的 CRUD 路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.exceptions import TaskNotFoundException
from app.models import Task, TaskStatus
from app.notifications import send_notification
from app.schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)) -> Task:
    """创建新任务。"""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=TaskStatus(task_in.status),
        due_date=task_in.due_date,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    """列出所有任务，可按状态筛选。"""
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == TaskStatus(status))
    stmt = stmt.order_by(Task.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)) -> Task:
    """通过 ID 获取指定任务。"""
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(task_id)
    return task


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
