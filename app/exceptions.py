"""Custom exceptions and error handlers for the Task Management API."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class TaskNotFoundException(Exception):
    """Raised when a task is not found by ID."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class ValidationException(Exception):
    """Raised when custom validation fails."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""

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
