"""外部天气 API 集成模块。

使用 wttr.in 免费 API（无需 API Key）获取任务 due_date 当天的天气预报。
请求失败时优雅降级返回 None。
"""

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import httpx

from config import cfg
from logger import create_logger

log = create_logger("weather", cfg.logging.level)

# 天气缓存：按 "日期|城市" 缓存查询结果，避免重复请求
_weather_cache: dict[str, dict[str, Any]] = {}
_weather_versions: dict[str, int] = {}


@lru_cache(maxsize=64)
def _get_cached_weather(cache_key: str, version: int) -> dict[str, Any] | None:
    """通过 lru_cache 获取缓存的天气数据。"""
    return _weather_cache.get(cache_key)


def _weather_cache_key(date: datetime, location: str) -> str:
    """生成天气缓存键。"""
    return f"{date.strftime('%Y-%m-%d')}|{location}"


async def fetch_weather(due_date: datetime | None) -> str | None:
    """获取 due_date 当天的天气描述。

    调用 wttr.in 免费 API，从 3 天预报中找到目标日期，
    返回人类可读的天气描述（如 "Sunny，25°C（12~25°C）"）。

    Args:
        due_date: 任务截止日期，为 None 时返回 None。

    Returns:
        天气描述字符串，获取失败时返回 None。
    """
    if due_date is None:
        return None

    if not getattr(cfg, "weather", None):
        return None

    weather_cfg = cfg.weather
    enabled = getattr(weather_cfg, "enabled", False)
    location = getattr(weather_cfg, "location", "Beijing")
    base_url = getattr(weather_cfg, "base_url", "https://wttr.in")
    timeout = int(getattr(weather_cfg, "timeout", 10))

    if not enabled:
        log.debug("天气功能未启用，跳过天气获取")
        return None

    # 检查缓存
    cache_key = _weather_cache_key(due_date, location)
    version = _weather_versions.get(cache_key, 0)
    cached = _get_cached_weather(cache_key, version)
    if cached is not None:
        return cached.get("description")

    # 调用 wttr.in API
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{base_url}/{location}"
            params = {"format": "j1"}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        log.warning("天气 API 请求失败: %s", e)
        return None
    except Exception as e:
        log.warning("获取天气数据时发生异常: %s", e)
        return None

    # 从 weather 列表中找到目标日期
    target_date = due_date.strftime("%Y-%m-%d")
    weather_list = data.get("weather", [])
    matching = [d for d in weather_list if d.get("date") == target_date]

    if not matching:
        log.info("未找到 %s 的天气预报数据（超出 3 天预报范围）", target_date)
        return None

    day = matching[0]
    max_temp = day["maxtempC"]
    min_temp = day["mintempC"]
    # 取中午时段（index=4，即12:00）的天气描述
    hourly = day.get("hourly", [])
    midday = hourly[4] if len(hourly) > 4 else hourly[0] if hourly else {}
    desc = midday.get("weatherDesc", [{}])[0].get("value", "未知")
    midday_temp = midday.get("tempC", max_temp)
    weather_desc = f"{desc}，{midday_temp}°C（{min_temp}~{max_temp}°C）"

    # 缓存结果
    _weather_cache[cache_key] = {"description": weather_desc}
    _weather_versions[cache_key] = _weather_versions.get(cache_key, 0) + 1

    log.info("已获取 %s 在 %s 的天气: %s", location, target_date, weather_desc)
    return weather_desc
