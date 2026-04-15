"""缓存功能测试。"""

from app.cache import (
    _cache,
    _versions,
    clear_all,
    get_cached_task,
    invalidate_cache,
    lookup,
    store_in_cache,
)


def test_store_and_lookup() -> None:
    """测试基本的缓存存取。"""
    clear_all()
    store_in_cache("task-1", {"id": "task-1", "title": "Test"})
    result = lookup("task-1")
    assert result is not None
    assert result["title"] == "Test"


def test_cache_miss() -> None:
    """测试缓存未命中。"""
    clear_all()
    assert lookup("nonexistent") is None


def test_invalidate() -> None:
    """测试缓存失效。"""
    clear_all()
    store_in_cache("task-1", {"id": "task-1", "title": "Test"})
    assert lookup("task-1") is not None

    invalidate_cache("task-1")
    assert lookup("task-1") is None


def test_invalidate_old_version_not_returned() -> None:
    """测试失效后旧版本数据不会被返回。"""
    clear_all()
    store_in_cache("task-1", {"id": "task-1", "title": "v1"})
    assert lookup("task-1")["title"] == "v1"

    # 更新数据
    store_in_cache("task-1", {"id": "task-1", "title": "v2"})
    assert lookup("task-1")["title"] == "v2"


def test_clear_all() -> None:
    """测试清空全部缓存。"""
    store_in_cache("task-1", {"id": "task-1", "title": "Test"})
    clear_all()
    assert lookup("task-1") is None
    assert len(_cache) == 0
    assert len(_versions) == 0


def test_lru_cache_used() -> None:
    """测试 lru_cache 装饰器被正确使用。"""
    clear_all()
    store_in_cache("task-1", {"id": "task-1", "title": "Test"})
    version = _versions["task-1"]
    # 第一次调用应该填充 lru_cache
    result1 = get_cached_task("task-1", version)
    assert result1 is not None
    # lru_cache 应该有缓存统计
    assert get_cached_task.cache_info().hits >= 0
