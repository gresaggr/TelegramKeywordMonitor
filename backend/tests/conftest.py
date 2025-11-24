# backend/tests/conftest.py
"""Pytest configuration and fixtures"""
import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import Base, get_async_session
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup test database"""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
async def clean_tables():
    """Clean all tables before each test"""
    async with engine.begin() as connection:
        # Delete data from all tables but keep structure
        for table in reversed(Base.metadata.sorted_tables):
            await connection.execute(table.delete())
    yield


@pytest.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Get test database session"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Get test HTTP client"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False
    ) as ac:
        yield ac


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        balance=100.0,
        is_active=True,
        default_api_id="2040",
        default_api_hash="b18441a1ff607e10a989891a5462e627",
        default_device_model="Test Device",
        default_system_version="Test OS",
        default_app_version="1.0.0"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_account_data() -> dict:
    """Sample account data for tests"""
    return {
        "phone_number": "+1234567890",
        "name": "Test Account",
        "api_id": "12345",
        "api_hash": "test_hash",
        "device_model": "Test Device",
        "system_version": "Test OS",
        "app_version": "1.0.0"
    }


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for tests"""
    return {
        "name": "Test Task",
        "whitelist_keywords": ["test", "keyword"],
        "blacklist_keywords": ["spam"],
        "monitored_channels": ["@testchannel", "-1001234567890"],
        "forward_to_chat_id": "-1009876543210",
        "replacements": {"old": "new"},
        "include_source_link": True
    }