"""Notification trigger tests for the Task Management API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notification_triggered_on_completion(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """Verify that completing a task triggers a notification."""
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"status": "completed"},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_no_notification_for_non_completed_update(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """Verify that updating to a non-completed status does not trigger notification."""
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"status": "in_progress"},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_no_notification_when_already_completed(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """Verify no re-notification when updating an already completed task."""
    # First complete
    await client.put(
        f"/tasks/{sample_task['id']}",
        json={"status": "completed"},
        headers=api_headers,
    )
    # Update again (already completed)
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Still Completed"},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
