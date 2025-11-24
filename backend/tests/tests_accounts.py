# backend/tests/test_accounts.py
"""Tests for account endpoints"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.models.user import User
from app.models.account import TelegramAccount, AccountStatus


class TestAccounts:
    """Test account management endpoints"""

    @pytest.mark.asyncio
    @patch('app.services.account_service.telegram_manager.create_client')
    @patch('app.services.billing_service.billing_service.check_balance_before_start')
    async def test_create_account_success(
            self,
            mock_check_balance,
            mock_create_client,
            client: AsyncClient,
            auth_headers: dict,
            sample_account_data: dict
    ):
        """Test successful account creation"""
        mock_check_balance.return_value = True
        mock_create_client.return_value = (AsyncMock(), False)

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/",
            headers=auth_headers,
            json=sample_account_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["phone_number"] == sample_account_data["phone_number"]
        assert data["name"] == sample_account_data["name"]

    @pytest.mark.asyncio
    async def test_create_account_unauthorized(
            self,
            client: AsyncClient,
            sample_account_data: dict
    ):
        """Test account creation without auth"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/",
            json=sample_account_data
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch('app.services.billing_service.billing_service.check_balance_before_start')
    async def test_create_account_insufficient_balance(
            self,
            mock_check_balance,
            client: AsyncClient,
            auth_headers: dict,
            sample_account_data: dict
    ):
        """Test account creation with insufficient balance"""
        mock_check_balance.return_value = False

        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/",
            headers=auth_headers,
            json=sample_account_data
        )
        assert response.status_code == 400
        assert "balance" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_accounts_empty(
            self,
            client: AsyncClient,
            auth_headers: dict
    ):
        """Test getting accounts when none exist"""
        response = await client.get(
            f"{settings.API_V1_PREFIX}/accounts/",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_account_limit(
            self,
            client: AsyncClient,
            auth_headers: dict,
            db_session,
            test_user: User
    ):
        """Test account creation limit"""
        # Create max accounts
        for i in range(settings.MAXIMUM_NUMBER_OF_ACCOUNTS):
            account = TelegramAccount(
                user_id=test_user.id,
                phone_number=f"+123456789{i}",
                api_id="12345",
                api_hash="hash",
                status=AccountStatus.ACTIVE
            )
            db_session.add(account)
        await db_session.commit()

        # Try to create one more
        response = await client.post(
            f"{settings.API_V1_PREFIX}/accounts/",
            headers=auth_headers,
            json={
                "phone_number": "+9999999999",
                "api_id": "12345",
                "api_hash": "hash"
            }
        )
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()


class TestAccountOperations:
    """Test account operations (start/stop/delete)"""

    @pytest.fixture
    async def test_account(self, db_session, test_user: User) -> TelegramAccount:
        """Create a test account"""
        account = TelegramAccount(
            user_id=test_user.id,
            phone_number="+1234567890",
            name="Test Account",
            api_id="12345",
            api_hash="hash",
            status=AccountStatus.ACTIVE,
            is_active=False
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        return account

    @pytest.mark.asyncio
    async def test_get_account(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount
    ):
        """Test getting specific account"""
        response = await client.get(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_account.id
        assert data["phone_number"] == test_account.phone_number

    @pytest.mark.asyncio
    async def test_update_account(
            self,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount
    ):
        """Test updating account"""
        response = await client.patch(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    @patch('app.services.account_service.telegram_manager.delete_client')
    async def test_delete_account(
            self,
            mock_delete_client,
            client: AsyncClient,
            auth_headers: dict,
            test_account: TelegramAccount
    ):
        """Test deleting account"""
        mock_delete_client.return_value = None

        response = await client.delete(
            f"{settings.API_V1_PREFIX}/accounts/{test_account.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(
            self,
            client: AsyncClient,
            auth_headers: dict
    ):
        """Test getting non-existent account"""
        response = await client.get(
            f"{settings.API_V1_PREFIX}/accounts/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
