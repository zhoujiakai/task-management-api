"""任务管理 API 的 CRUD 测试。"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, api_headers: dict[str, str]) -> None:
    due = datetime.now(timezone.utc) + timedelta(days=7)
    response = await client.post(
        "/tasks",
        json={
            "title": "New Task",
            "description": "Task description",
            "status": "pending",
            "due_date": due.isoformat(),
        },
        headers=api_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["description"] == "Task description"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    response = await client.get("/tasks", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Task"


@pytest.mark.asyncio
async def test_list_tasks_with_status_filter(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    response = await client.get("/tasks?status=pending", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(t["status"] == "pending" for t in data)


@pytest.mark.asyncio
async def test_get_task(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    response = await client.get(f"/tasks/{sample_task['id']}", headers=api_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"


@pytest.mark.asyncio
async def test_update_task(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Updated Task"},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Task"


@pytest.mark.asyncio
async def test_delete_task(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    response = await client.delete(
        f"/tasks/{sample_task['id']}", headers=api_headers
    )
    assert response.status_code == 204

    # 验证已删除
    response = await client.get(f"/tasks/{sample_task['id']}", headers=api_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_task(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.get("/tasks/nonexistent-id", headers=api_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_task(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.delete("/tasks/nonexistent-id", headers=api_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient) -> None:
    response = await client.get("/tasks")
    assert response.status_code == 401
