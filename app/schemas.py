"""任务管理 API 的 Pydantic 请求/响应模式。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    """创建新任务的请求模式。"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: str = "pending"
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is not None and v <= datetime.now(tz=v.tzinfo):
            raise ValueError("due_date must be in the future")
        return v

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        from app.models import TaskStatus

        allowed = [s.value for s in TaskStatus]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class TaskUpdate(BaseModel):
    """更新已有任务的请求模式。"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is not None and v <= datetime.now(tz=v.tzinfo):
            raise ValueError("due_date must be in the future")
        return v

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.models import TaskStatus

        allowed = [s.value for s in TaskStatus]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class TaskResponse(BaseModel):
    """任务响应数据的模式。"""

    id: str
    title: str
    description: str | None
    status: str
    due_date: datetime | None
    weather_info: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
