"""Exception response format tests for the Task Management API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_not_found_response_format(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.get("/tasks/nonexistent-id", headers=api_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "nonexistent-id" in data["detail"]


@pytest.mark.asyncio
async def test_task_not_found_on_delete(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.delete("/tasks/nonexistent-id", headers=api_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_task_not_found_on_update(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.put(
        "/tasks/nonexistent-id",
        json={"title": "Update"},
        headers=api_headers,
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_unauthorized_response_format(client: AsyncClient) -> None:
    response = await client.get("/tasks")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_validation_error_response_format(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/tasks",
        json={"title": ""},
        headers=api_headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
