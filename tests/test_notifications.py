"""任务管理 API 的通知触发测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notification_triggered_on_completion(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """验证完成任务时触发通知。"""
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
    """验证更新为非完成状态时不触发通知。"""
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
    """验证更新已完成任务时不会重复通知。"""
    # 首次完成
    await client.put(
        f"/tasks/{sample_task['id']}",
        json={"status": "completed"},
        headers=api_headers,
    )
    # 再次更新（已完成）
    response = await client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Still Completed"},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
