# backend/tests/test_billing.py
"""Tests for billing service"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import BillingService
from app.models.user import User
from app.models.account import TelegramAccount, AccountStatus, MonitoringTask


class TestBillingService:
    """Test billing calculations and operations"""

    @pytest.mark.asyncio
    async def test_calculate_hourly_cost_empty(self):
        """Test hourly cost calculation with no services"""
        cost = BillingService.calculate_hourly_cost(0, 0)
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_calculate_hourly_cost_one_one(self):
        """Test hourly cost: 1 account × 1 task = 200 RUB/month"""
        cost = BillingService.calculate_hourly_cost(1, 1)
        expected = 200.0 / (30 * 24)  # 200 RUB per month / 720 hours
        assert cost == round(expected, 4)

    @pytest.mark.asyncio
    async def test_calculate_hourly_cost_one_five(self):
        """Test hourly cost: 1 account × 5 tasks = 250 RUB/month"""
        cost = BillingService.calculate_hourly_cost(1, 5)
        expected = 250.0 / (30 * 24)
        assert cost == round(expected, 4)

    @pytest.mark.asyncio
    async def test_calculate_hourly_cost_five_five(self):
        """Test hourly cost: 5 accounts × 5 tasks = 1000 RUB/month"""
        cost = BillingService.calculate_hourly_cost(5, 5)
        expected = 1000.0 / (30 * 24)
        assert cost == round(expected, 4)

    @pytest.mark.asyncio
    async def test_get_user_active_stats_empty(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test getting stats with no active services"""
        accounts, tasks = await BillingService.get_user_active_stats(
            test_user.id, db_session
        )
        assert accounts == 0
        assert tasks == 0

    @pytest.mark.asyncio
    async def test_get_user_active_stats_with_data(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test getting stats with active services"""
        # Create active account
        account = TelegramAccount(
            user_id=test_user.id,
            phone_number="+1234567890",
            api_id="12345",
            api_hash="hash",
            status=AccountStatus.ACTIVE,
            is_active=True
        )
        db_session.add(account)
        await db_session.flush()

        # Create active task
        task = MonitoringTask(
            account_id=account.id,
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

        accounts, tasks = await BillingService.get_user_active_stats(
            test_user.id, db_session
        )
        assert accounts == 1
        assert tasks == 1

    @pytest.mark.asyncio
    async def test_check_balance_before_start_sufficient(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test balance check with sufficient balance"""
        result = await BillingService.check_balance_before_start(
            test_user.id, db_session
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_balance_before_start_insufficient(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test balance check with insufficient balance"""
        test_user.balance = 0.0
        await db_session.commit()

        result = await BillingService.check_balance_before_start(
            test_user.id, db_session
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_deduct_balance(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test balance deduction"""
        # Create active services
        account = TelegramAccount(
            user_id=test_user.id,
            phone_number="+1234567890",
            api_id="12345",
            api_hash="hash",
            status=AccountStatus.ACTIVE,
            is_active=True
        )
        db_session.add(account)
        await db_session.flush()

        task = MonitoringTask(
            account_id=account.id,
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

        initial_balance = test_user.balance
        new_balance = await BillingService.deduct_balance(test_user.id, db_session)

        assert new_balance is not None
        assert new_balance < initial_balance

    @pytest.mark.asyncio
    async def test_deduct_balance_no_services(
            self,
            db_session: AsyncSession,
            test_user: User
    ):
        """Test balance deduction with no active services"""
        initial_balance = test_user.balance
        new_balance = await BillingService.deduct_balance(test_user.id, db_session)

        assert new_balance == initial_balance
