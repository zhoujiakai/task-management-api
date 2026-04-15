"""天气 API 集成测试。"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient

from app.weather import fetch_weather


@pytest.fixture(autouse=True)
def clear_weather_cache() -> None:
    """每个测试前后清空天气缓存。"""
    import app.weather as weather_mod

    weather_mod._weather_cache.clear()
    weather_mod._weather_versions.clear()
    weather_mod._get_cached_weather.cache_clear()
    yield
    weather_mod._weather_cache.clear()
    weather_mod._weather_versions.clear()
    weather_mod._get_cached_weather.cache_clear()


@pytest.mark.asyncio
async def test_fetch_weather_returns_none_when_no_due_date() -> None:
    """无 due_date 时返回 None。"""
    result = await fetch_weather(None)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_weather_returns_none_when_disabled() -> None:
    """天气功能禁用时返回 None。"""
    future_date = datetime.now(timezone.utc) + timedelta(days=3)
    # config 中 weather.enabled=true 但 api_key 为空
    with patch("app.weather.cfg") as mock_cfg:
        mock_weather = type("W", (), {"enabled": True, "api_key": "", "location": "Beijing"})()
        mock_cfg.weather = mock_weather
        result = await fetch_weather(future_date)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_weather_success() -> None:
    """天气 API 返回成功时，解析并缓存天气描述。"""
    future_date = datetime.now(timezone.utc) + timedelta(days=3)
    target_date_str = future_date.strftime("%Y-%m-%d")

    mock_response_data = {
        "list": [
            {
                "dt_txt": f"{target_date_str} 12:00:00",
                "main": {"temp": 22.5},
                "weather": [{"description": "晴"}],
            },
        ]
    }

    mock_resp = Mock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.weather.cfg") as mock_cfg,
        patch("app.weather.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_weather = type("W", (), {"enabled": True, "api_key": "test-key", "location": "Beijing"})()
        mock_cfg.weather = mock_weather

        result = await fetch_weather(future_date)

    assert result is not None
    assert "晴" in result
    assert "22.5°C" in result


@pytest.mark.asyncio
async def test_fetch_weather_handles_api_failure() -> None:
    """天气 API 失败时优雅降级，返回 None。"""
    future_date = datetime.now(timezone.utc) + timedelta(days=3)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.weather.cfg") as mock_cfg,
        patch("app.weather.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_weather = type("W", (), {"enabled": True, "api_key": "test-key", "location": "Beijing"})()
        mock_cfg.weather = mock_weather

        result = await fetch_weather(future_date)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_weather_no_matching_date() -> None:
    """预报数据中无匹配日期时返回 None（如超过 5 天预报范围）。"""
    far_future = datetime.now(timezone.utc) + timedelta(days=10)

    mock_response_data = {"list": []}

    mock_resp = Mock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.weather.cfg") as mock_cfg,
        patch("app.weather.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_weather = type("W", (), {"enabled": True, "api_key": "test-key", "location": "Beijing"})()
        mock_cfg.weather = mock_weather

        result = await fetch_weather(far_future)

    assert result is None


@pytest.mark.asyncio
async def test_task_create_with_weather_info(
    client: AsyncClient, api_headers: dict[str, str]
) -> None:
    """创建任务时，响应中包含 weather_info 字段（可能为 None）。"""
    due = datetime.now(timezone.utc) + timedelta(days=7)
    response = await client.post(
        "/tasks",
        json={
            "title": "Weather Task",
            "description": "Check weather",
            "due_date": due.isoformat(),
        },
        headers=api_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "weather_info" in data
    # 当前未配置真实 API Key，weather_info 应为 None
    assert data["weather_info"] is None


@pytest.mark.asyncio
async def test_task_get_with_weather_info(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """获取任务时，响应中包含 weather_info 字段。"""
    response = await client.get(
        f"/tasks/{sample_task['id']}", headers=api_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "weather_info" in data


@pytest.mark.asyncio
async def test_task_list_includes_weather_field(
    client: AsyncClient, api_headers: dict[str, str], sample_task: dict
) -> None:
    """任务列表中每项也包含 weather_info 字段（list 直接返回 ORM，字段为 None）。"""
    response = await client.get("/tasks", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for task in data:
        assert "weather_info" in task
