# backend/tests/test_tasks.py
"""Tests for task endpoints"""
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models.user import User
from app.models.account import TelegramAccount, AccountStatus, MonitoringTask


class TestTasks:
    """Test monitoring task endpoints"""

    @pytest.fixture
    async def test_account(self, db_session, test_user: User) -> TelegramAccount:
        """Create a test account"""
        account = TelegramAccount(
            user_id=test_user.id,
            phone_number="+1234567890",
            api_id="12345",
            api_hash="hash",
            status=AccountStatus.ACTIVE,
            is_active=True
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        return account

    @pytest.mark.asyncio
    async def test_create_task_success(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            sample_task_data: dict
    ):
        """Test successful task creation"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks",
            headers=auth_headers,
            json=sample_task_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_task_data["name"]
        assert data["account_id"] == test_account.id
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_task_too_many_channels(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            sample_task_data: dict
    ):
        """Test task creation with too many channels"""
        sample_task_data["monitored_channels"] = [f"@channel{i}" for i in range(10)]

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks",
            headers=auth_headers,
            json=sample_task_data
        )
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_task_keywords_limit(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            sample_task_data: dict
    ):
        """Test task creation with too many keywords"""
        sample_task_data["whitelist_keywords"] = [f"keyword{i}" for i in range(15)]

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks",
            headers=auth_headers,
            json=sample_task_data
        )
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_task(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            db_session
    ):
        """Test updating task"""
        # Create task
        task = MonitoringTask(
            account_id=test_account.id,
            name="Original Task",
            whitelist_keywords="[]",
            blacklist_keywords="[]",
            monitored_channels='["@test"]',
            forward_to_chat_id="-1001234567890",
            replacements="{}",
            is_active=True
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Update task
        response = await client.patch(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks/{task.id}",
            headers=auth_headers,
            json={"name": "Updated Task"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task"

    @pytest.mark.asyncio
    async def test_start_task(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            db_session
    ):
        """Test starting task"""
        task = MonitoringTask(
            account_id=test_account.id,
            name="Test Task",
            whitelist_keywords="[]",
            blacklist_keywords="[]",
            monitored_channels='["@test"]',
            forward_to_chat_id="-1001234567890",
            replacements="{}",
            is_active=False
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks/{task.id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_stop_task(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            db_session
    ):
        """Test stopping task"""
        task = MonitoringTask(
            account_id=test_account.id,
            name="Test Task",
            whitelist_keywords="[]",
            blacklist_keywords="[]",
            monitored_channels='["@test"]',
            forward_to_chat_id="-1001234567890",
            replacements="{}",
            is_active=True
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks/{task.id}/stop",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_task(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            db_session
    ):
        """Test deleting task"""
        task = MonitoringTask(
            account_id=test_account.id,
            name="Test Task",
            whitelist_keywords="[]",
            blacklist_keywords="[]",
            monitored_channels='["@test"]',
            forward_to_chat_id="-1001234567890",
            replacements="{}",
            is_active=True
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.delete(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks/{task.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_task_limit(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount,
            db_session
    ):
        """Test task creation limit"""
        # Create max tasks
        for i in range(settings.MAXIMUM_NUMBER_OF_TASKS):
            task = MonitoringTask(
                account_id=test_account.id,
                name=f"Task {i}",
                whitelist_keywords="[]",
                blacklist_keywords="[]",
                monitored_channels='["@test"]',
                forward_to_chat_id="-1001234567890",
                replacements="{}"
            )
            db_session.add(task)
        await db_session.commit()

        # Try to create one more
        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}/tasks",
            headers=auth_headers,
            json={
                "name": "Extra Task",
                "monitored_channels": ["@test"],
                "forward_to_chat_id": "-1001234567890"
            }
        )
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()
