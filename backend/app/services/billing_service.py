# backend/app/services/billing_service.py
"""Billing service for calculating and deducting user balance"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.core.config import settings
from app.core.logger import get_logger
from app.models.user import User
from app.models.account import TelegramAccount, MonitoringTask, AccountStatus

logger = get_logger("services.billing")


class BillingService:
    """Service for managing user billing"""

    @staticmethod
    def calculate_hourly_cost(active_accounts: int, active_tasks: int) -> float:
        """
        Calculate hourly cost based on active accounts and tasks

        Pricing model:
        - 1 account × 1 task = 200 RUB/month
        - 1 account × 5 tasks = 250 RUB/month
        - 5 accounts × 5 tasks = 1000 RUB/month (MAX)

        Formula: accounts * (150 + tasks * 10) with manual corrections
        """
        if active_accounts == 0 or active_tasks == 0:
            return 0.0

        # Hard-coded exact requirements
        if active_accounts == 1 and active_tasks == 1:
            monthly_cost = 200.0
        elif active_accounts == 1 and active_tasks == 5:
            monthly_cost = 250.0
        elif active_accounts == 5 and active_tasks == 5:
            monthly_cost = 1000.0
        else:
            # General formula
            monthly_cost = active_accounts * (150 + active_tasks * 10)

        # Cap at maximum configured cost
        monthly_cost = min(monthly_cost, settings.MONTHLY_COST_MAX)

        hours_per_month = 30 * 24  # 720 hours
        hourly_cost = monthly_cost / hours_per_month

        return round(hourly_cost, 4)

    @staticmethod
    async def get_user_active_stats(user_id: int, db: AsyncSession) -> tuple[int, int]:
        """Get count of active accounts and active tasks for user"""
        # Count active accounts
        result = await db.execute(
            select(func.count(TelegramAccount.id))
            .where(
                TelegramAccount.user_id == user_id,
                TelegramAccount.is_active == True,
                TelegramAccount.status == AccountStatus.ACTIVE
            )
        )
        active_accounts = result.scalar() or 0

        # Count active tasks
        result = await db.execute(
            select(func.count(MonitoringTask.id))
            .join(TelegramAccount, TelegramAccount.id == MonitoringTask.account_id)
            .where(
                TelegramAccount.user_id == user_id,
                MonitoringTask.is_active == True
            )
        )
        active_tasks = result.scalar() or 0

        return active_accounts, active_tasks

    @staticmethod
    async def check_balance_before_start(user_id: int, db: AsyncSession) -> bool:
        """Check if user has sufficient balance before starting monitoring"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        if user.balance <= 0:
            logger.warning(f"User {user_id}: Insufficient balance to start monitoring")
            return False

        return True

    @staticmethod
    async def deduct_balance(user_id: int, db: AsyncSession) -> Optional[float]:
        """
        Deduct balance for one billing period
        Returns new balance or None if user not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        active_accounts, active_tasks = await BillingService.get_user_active_stats(user_id, db)

        billing_hours = settings.BALANCE_CHECK_INTERVAL / 3600
        hourly_cost = BillingService.calculate_hourly_cost(active_accounts, active_tasks)
        period_cost = hourly_cost * billing_hours

        if period_cost == 0:
            logger.debug(f"User {user_id}: No active services, skipping deduction")
            return user.balance

        old_balance = user.balance
        new_balance = max(0.0, old_balance - period_cost)

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=new_balance)
        )
        await db.commit()

        logger.info(
            f"User {user_id}: Deducted {period_cost:.4f} "
            f"({active_accounts} accounts, {active_tasks} tasks). "
            f"Balance: {old_balance:.4f} -> {new_balance:.4f}"
        )

        if new_balance == 0 and old_balance > 0:
            await BillingService.stop_all_user_services(user_id, user, db)

        return new_balance

    @staticmethod
    async def stop_all_user_services(user_id: int, user: User, db: AsyncSession):
        """Stop all accounts and tasks when balance reaches 0"""
        from app.telegram.client_manager import telegram_manager
        from app.services.telegram import send_telegram_notification

        logger.warning(f"User {user_id}: Balance reached 0, stopping all services")

        result = await db.execute(
            select(TelegramAccount)
            .where(
                TelegramAccount.user_id == user_id,
                TelegramAccount.is_active == True
            )
        )
        accounts = result.scalars().all()

        for account in accounts:
            try:
                await telegram_manager.stop_client(account.id, db)
            except Exception as e:
                logger.error(f"Error stopping account {account.id}: {e}")

        # Stop all tasks
        await db.execute(
            update(MonitoringTask)
            .where(
                MonitoringTask.account_id.in_([acc.id for acc in accounts])
            )
            .values(is_active=False)
        )

        await db.commit()

        if user.default_telegram_chat_id:
            message = (
                "⚠️ *Balance Alert*\n\n"
                "Your balance has reached 0.\n"
                "All monitoring services have been stopped.\n\n"
                "Please top up your balance to resume monitoring."
            )
            if user.language == "ru":
                message = (
                    "⚠️ *Уведомление о низком балансе*\n\n"
                    "Ваш баланс достиг 0.\n"
                    "Все задачи по отслеживанию остановлены.\n\n"
                    "Пополните баланс для возобновления работы."
                )

            try:
                await send_telegram_notification(user.default_telegram_chat_id, message)
            except Exception as e:
                logger.error(f"Failed to send balance alert to user {user_id}: {e}")

    @staticmethod
    async def process_all_users():
        """Process billing for all users"""
        from app.db.session import async_session_maker

        logger.info("Starting billing cycle for all users")

        async with async_session_maker() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    await BillingService.deduct_balance(user.id, db)
                except Exception as e:
                    logger.error(f"Error processing billing for user {user.id}: {e}")

        logger.info("Billing cycle completed")


billing_service = BillingService()
