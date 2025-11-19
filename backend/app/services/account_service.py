# backend/app/services/account_service.py
"""Service for Telegram account operations"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.account import TelegramAccount, AccountStatus, AccountNotification, MonitoringTask
from app.models.user import User
from app.schemas.account import (
    TelegramAccountCreate,
    TelegramAccountUpdate,
    TelegramAccountResponse,
    AccountNotificationResponse,
    MonitoringTaskCreate,
    MonitoringTaskUpdate,
    MonitoringTaskResponse
)
from app.telegram.client_manager import telegram_manager
from app.core.logger import get_logger
from .task_service import TaskService
from .notification_service import NotificationService
from .billing_service import billing_service
from ..core.config import settings

logger = get_logger("services.account")


class AccountService:
    """Service for managing Telegram accounts"""

    def __init__(self):
        self.task_service = TaskService()
        self.notification_service = NotificationService()

    async def create_account(
            self,
            account_data: TelegramAccountCreate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Create a new Telegram account"""
        # Check balance
        if not await billing_service.check_balance_before_start(user.id, db):
            raise ValueError("Insufficient balance. Please top up your balance to add accounts.")

        # Check for duplicate phone number
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.user_id == user.id,
                TelegramAccount.phone_number == account_data.phone_number
            )
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Account with phone number {account_data.phone_number} already exists")

        # Check if phone number is active on other users
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.phone_number == account_data.phone_number,
                TelegramAccount.is_active == True,
                TelegramAccount.user_id != user.id
            )
        )
        active_on_other_user = result.scalar_one_or_none()
        if active_on_other_user:
            raise ValueError(
                f"Account with phone number {account_data.phone_number} is already active on another account")

        # Check account limit
        result = await db.execute(
            select(func.count(TelegramAccount.id))
            .where(TelegramAccount.user_id == user.id)
        )
        account_count = result.scalar()

        if account_count >= settings.MAXIMUM_NUMBER_OF_ACCOUNTS:
            raise ValueError(f"Maximum number of accounts ({settings.MAXIMUM_NUMBER_OF_ACCOUNTS}) reached.")

        # Create account
        new_account = TelegramAccount(
            user_id=user.id,
            phone_number=account_data.phone_number,
            name=account_data.name,
            api_id=account_data.api_id,
            api_hash=account_data.api_hash,
            device_model=account_data.device_model,
            system_version=account_data.system_version,
            app_version=account_data.app_version,
            proxy_host=account_data.proxy.host if account_data.proxy else None,
            proxy_port=account_data.proxy.port if account_data.proxy else None,
            proxy_username=account_data.proxy.username if account_data.proxy else None,
            proxy_password=account_data.proxy.password if account_data.proxy else None,
            status=AccountStatus.INITIALIZING
        )

        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)

        try:
            client, needs_auth = await telegram_manager.create_client(new_account, db)

            if not needs_auth:
                new_account.status = AccountStatus.ACTIVE
                new_account.is_active = False
                await db.commit()

            await db.refresh(new_account)
            return await self._to_response(new_account, db)

        except Exception as e:
            logger.error(f"Error creating account: {e}")
            new_account.status = AccountStatus.ERROR
            new_account.error_message = str(e)
            await db.commit()
            raise

    async def update_account(
            self,
            account_id: int,
            account_data: TelegramAccountUpdate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Update account settings"""
        account = await self._get_user_account(account_id, user, db)

        # Update fields
        if account_data.name is not None:
            account.name = account_data.name
        if account_data.api_id is not None:
            account.api_id = account_data.api_id
        if account_data.api_hash is not None:
            account.api_hash = account_data.api_hash
        if account_data.device_model is not None:
            account.device_model = account_data.device_model
        if account_data.system_version is not None:
            account.system_version = account_data.system_version
        if account_data.app_version is not None:
            account.app_version = account_data.app_version
        if account_data.proxy is not None:
            account.proxy_host = account_data.proxy.host
            account.proxy_port = account_data.proxy.port
            account.proxy_username = account_data.proxy.username
            account.proxy_password = account_data.proxy.password

        await db.commit()
        await db.refresh(account)
        return await self._to_response(account, db)

    async def verify_code(
            self,
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Verify authentication code"""
        account = await self._get_user_account(account_id, user, db)
        await telegram_manager.verify_code(account_id, code, two_fa_password, db)
        await db.refresh(account)
        return await self._to_response(account, db)

    async def get_accounts(
            self,
            user: User,
            db: AsyncSession
    ) -> List[TelegramAccountResponse]:
        """Get all accounts for user"""
        result = await db.execute(
            select(TelegramAccount)
            .where(TelegramAccount.user_id == user.id)
            .order_by(TelegramAccount.created_at.desc())
        )
        accounts = result.scalars().all()
        return [await self._to_response(acc, db) for acc in accounts]

    async def get_account(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Get specific account"""
        account = await self._get_user_account(account_id, user, db)
        return await self._to_response(account, db)

    async def start_account(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Start account monitoring"""
        account = await self._get_user_account(account_id, user, db)

        # Check balance before starting
        if not await billing_service.check_balance_before_start(user.id, db):
            raise ValueError("Insufficient balance. Please top up your balance to start monitoring.")

        if account.status in [AccountStatus.AWAITING_CODE, AccountStatus.AWAITING_2FA]:
            raise ValueError("Please complete authorization first")

        client = telegram_manager.clients.get(account_id)
        if not client:
            client, needs_auth = await telegram_manager.create_client(account, db)
            if needs_auth:
                raise ValueError("Authorization required")

        await telegram_manager.start_monitoring(account_id, db)

        account.error_message = None
        account.status = AccountStatus.ACTIVE
        account.is_active = True
        await db.commit()
        await db.refresh(account)

        return await self._to_response(account, db)

    async def stop_account(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Stop account monitoring"""
        account = await self._get_user_account(account_id, user, db)
        await telegram_manager.stop_client(account_id, db)
        await db.refresh(account)
        return await self._to_response(account, db)

    async def delete_account(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ):
        """Delete account"""
        account = await self._get_user_account(account_id, user, db)
        await telegram_manager.delete_client(account, account_id, db)
        await db.execute(delete(TelegramAccount).where(TelegramAccount.id == account_id))
        await db.commit()

    # Monitoring task methods (delegate to TaskService)
    async def create_monitoring_task(
            self,
            account_id: int,
            task_data: MonitoringTaskCreate,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Create monitoring task"""
        # Check if forward_to_chat_id is accessible
        account = await self._get_user_account(account_id, user, db)

        # Verify chat access
        client = telegram_manager.clients.get(account_id)
        if client:
            try:
                await client.get_chat(task_data.forward_to_chat_id)
            except Exception as e:
                logger.error(f"Cannot access chat {task_data.forward_to_chat_id}: {e}")
                raise ValueError(
                    f"Account doesn't have access to chat {task_data.forward_to_chat_id}. Please check the chat ID and ensure the account is a member.")

        result = await self.task_service.create_task(account_id, task_data, user, db)

        # Update monitoring if account is active
        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return result

    async def update_monitoring_task(
            self,
            account_id: int,
            task_id: int,
            task_data: MonitoringTaskUpdate,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Update monitoring task"""
        result = await self.task_service.update_task(account_id, task_id, task_data, user, db)

        # Update monitoring if account is active
        account = await self._get_user_account(account_id, user, db)
        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return result

    async def start_monitoring_task(
            self,
            account_id: int,
            task_id: int,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Start monitoring task"""
        # Check balance before starting
        if not await billing_service.check_balance_before_start(user.id, db):
            raise ValueError("Insufficient balance. Please top up your balance to start task.")

        result = await self.task_service.toggle_task_status(account_id, task_id, True, user, db)

        account = await self._get_user_account(account_id, user, db)
        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return result

    async def stop_monitoring_task(
            self,
            account_id: int,
            task_id: int,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Stop monitoring task"""
        result = await self.task_service.toggle_task_status(account_id, task_id, False, user, db)

        account = await self._get_user_account(account_id, user, db)
        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return result

    async def delete_monitoring_task(
            self,
            account_id: int,
            task_id: int,
            user: User,
            db: AsyncSession
    ):
        """Delete monitoring task"""
        await self.task_service.delete_task(account_id, task_id, user, db)

        account = await self._get_user_account(account_id, user, db)
        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

    # Notification methods (delegate to NotificationService)
    async def get_notifications(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ) -> List[AccountNotificationResponse]:
        """Get account notifications"""
        return await self.notification_service.get_notifications(account_id, user, db)

    async def mark_notification_read(
            self,
            account_id: int,
            notification_id: int,
            user: User,
            db: AsyncSession
    ):
        """Mark notification as read"""
        await self.notification_service.mark_notification_read(
            account_id, notification_id, user, db
        )

    # Helper methods
    async def _get_user_account(
            self,
            account_id: int,
            user: User,
            db: AsyncSession
    ) -> TelegramAccount:
        """Get account and verify ownership"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        return account

    async def _to_response(
            self,
            account: TelegramAccount,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Convert account to response model"""
        # Count unread notifications
        result = await db.execute(
            select(func.count(AccountNotification.id))
            .where(
                AccountNotification.account_id == account.id,
                AccountNotification.is_read == False
            )
        )
        unread_count = result.scalar() or 0

        # Get monitoring tasks
        result = await db.execute(
            select(MonitoringTask).where(MonitoringTask.account_id == account.id)
        )
        tasks = result.scalars().all()

        return TelegramAccountResponse(
            id=account.id,
            phone_number=account.phone_number,
            name=account.name,
            status=account.status,
            is_active=account.is_active,
            error_message=account.error_message,
            unread_notifications_count=unread_count,
            created_at=account.created_at,
            last_activity=account.last_activity,
            monitoring_tasks=[self.task_service.task_to_response(t) for t in tasks]
        )


# Create singleton instance
AccountService = AccountService()
