"""外部天气 API 集成模块。

使用 OpenWeatherMap 免费 API 获取任务 due_date 当天的天气预报。
当 API Key 未配置或请求失败时，优雅降级返回 None。
"""

from datetime import datetime
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

    调用 OpenWeatherMap 5 天预报 API，找到目标日期的预报数据，
    返回人类可读的天气描述（如 "多云，15.2°C"）。

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
    api_key = getattr(weather_cfg, "api_key", "")
    location = getattr(weather_cfg, "location", "Beijing")
    base_url = getattr(weather_cfg, "base_url", "https://api.openweathermap.org/data/2.5/forecast")
    timeout = getattr(weather_cfg, "timeout", 10)

    if not enabled or not api_key:
        log.debug("天气功能未启用或未配置 API Key，跳过天气获取")
        return None

    # 检查缓存
    cache_key = _weather_cache_key(due_date, location)
    version = _weather_versions.get(cache_key, 0)
    cached = _get_cached_weather(cache_key, version)
    if cached is not None:
        return cached.get("description")

    # 调用 OpenWeatherMap API
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric",
                "cnt": 40,
            }
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        log.warning("天气 API 请求失败: %s", e)
        return None
    except Exception as e:
        log.warning("获取天气数据时发生异常: %s", e)
        return None

    # 从预报列表中找到目标日期的条目
    target_date = due_date.strftime("%Y-%m-%d")
    matching_items = [
        item
        for item in data.get("list", [])
        if item.get("dt_txt", "").startswith(target_date)
    ]

    if not matching_items:
        log.info("未找到 %s 的天气预报数据（可能超出 5 天预报范围）", target_date)
        return None

    # 取目标日期中午 12:00 附近的预报（或第一个可用的）
    best = min(
        matching_items,
        key=lambda item: abs(int(item.get("dt_txt", "").split(" ")[1][:2]) - 12),
    )

    temp = best["main"]["temp"]
    description = best["weather"][0]["description"] if best.get("weather") else "未知"
    weather_desc = f"{description}，{temp:.1f}°C"

    # 缓存结果
    _weather_cache[cache_key] = {"description": weather_desc}
    _weather_versions[cache_key] = _weather_versions.get(cache_key, 0) + 1

    log.info("已获取 %s 在 %s 的天气: %s", location, target_date, weather_desc)
    return weather_desc
