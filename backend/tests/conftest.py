"""测试套件的 Pytest 固件。"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db
from app.main import app
from app.models.task import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_API_KEY = "test-api-key-123"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """在每个测试前创建表，测试后删除表。"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """提供异步 HTTP 测试客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def api_headers() -> dict[str, str]:
    """提供有效的 API 密钥请求头。"""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
async def sample_task(client: AsyncClient, api_headers: dict[str, str]) -> dict:
    """创建示例任务并返回其数据。"""
    from datetime import datetime, timedelta, timezone

    due = datetime.now(timezone.utc) + timedelta(days=7)
    response = await client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "description": "A test task",
            "status": "pending",
            "due_date": due.isoformat(),
        },
        headers=api_headers,
    )
    return response.json()
