"""任务缓存模块，使用 functools.lru_cache 实现单任务查询缓存。"""

from functools import lru_cache
from typing import Any

# 内部缓存存储（序列化后的任务数据）
_cache: dict[str, dict[str, Any]] = {}
# 版本号，用于缓存失效
_versions: dict[str, int] = {}


@lru_cache(maxsize=128)
def get_cached_task(task_id: str, version: int) -> dict[str, Any] | None:
    """通过 lru_cache 获取缓存的任务数据。version 参数变更时自动失效旧条目。"""
    return _cache.get(task_id)


def store_in_cache(task_id: str, data: dict[str, Any]) -> None:
    """将任务数据存入缓存。"""
    _cache[task_id] = data
    _versions[task_id] = _versions.get(task_id, 0) + 1


def invalidate_cache(task_id: str) -> None:
    """使缓存条目失效。"""
    _cache.pop(task_id, None)
    _versions[task_id] = _versions.get(task_id, 0) + 1


def lookup(task_id: str) -> dict[str, Any] | None:
    """查找任务缓存。"""
    version = _versions.get(task_id, 0)
    return get_cached_task(task_id, version)


def clear_all() -> None:
    """清空全部缓存。"""
    _cache.clear()
    _versions.clear()
    get_cached_task.cache_clear()
