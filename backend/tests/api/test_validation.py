"""任务管理 API 的输入验证测试。"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_with_empty_title(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/tasks",
        json={"title": ""},
        headers=api_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_with_past_due_date(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    response = await client.post(
        "/tasks",
        json={
            "title": "Past Task",
            "due_date": past.isoformat(),
        },
        headers=api_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_with_invalid_status(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/tasks",
        json={"title": "Bad Status", "status": "invalid"},
        headers=api_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_task_with_past_due_date(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"due_date": past.isoformat()},
        headers=api_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_with_valid_future_date(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    future = datetime.now(timezone.utc) + timedelta(days=30)
    response = await client.post(
        "/tasks",
        json={
            "title": "Future Task",
            "due_date": future.isoformat(),
        },
        headers=api_headers,
    )
    assert response.status_code == 201
