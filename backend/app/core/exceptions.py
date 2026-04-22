"""任务管理 API 的自定义异常和错误处理器。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class TaskNotFoundException(Exception):
    """通过 ID 未找到任务时抛出。"""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class ValidationException(Exception):
    """自定义验证失败时抛出。"""

    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI 应用上注册自定义异常处理器。"""

    @app.exception_handler(TaskNotFoundException)
    async def task_not_found_handler(
        request: Request, exc: TaskNotFoundException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Task with id '{exc.task_id}' not found"},
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(
        request: Request, exc: ValidationException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": exc.detail},
        )
