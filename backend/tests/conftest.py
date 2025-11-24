# backend/tests/conftest.py
"""Pytest configuration and fixtures"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
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

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session


app.dependency_overrides[get_async_session] = get_test_session


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def session():
     async with new_session() as session:
        yield session


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac



@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
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
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login/",
        json={"email": "test@example.com", "password": "testpass123"}
    )
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
