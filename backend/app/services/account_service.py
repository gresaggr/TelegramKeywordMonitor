import json
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

logger = get_logger("services.account")


class AccountService:
    @staticmethod
    async def create_account(
            account_data: TelegramAccountCreate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Create a new Telegram account"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.user_id == user.id,
                TelegramAccount.phone_number == account_data.phone_number
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Account with phone number {account_data.phone_number} already exists")

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
            return await AccountService._to_response(new_account, db)

        except Exception as e:
            logger.error(f"Error creating account: {e}")
            new_account.status = AccountStatus.ERROR
            new_account.error_message = str(e)
            await db.commit()
            raise

    @staticmethod
    async def update_account(
            account_id: int,
            account_data: TelegramAccountUpdate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Update account settings"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

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
        return await AccountService._to_response(account, db)

    @staticmethod
    async def verify_code(
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            user: User,
            db: AsyncSession
    ) -> TelegramAccountResponse:
        """Verify authentication code"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        await telegram_manager.verify_code(account_id, code, two_fa_password, db)
        await db.refresh(account)
        return await AccountService._to_response(account, db)

    @staticmethod
    async def get_accounts(user: User, db: AsyncSession) -> List[TelegramAccountResponse]:
        """Get all accounts for user"""
        result = await db.execute(
            select(TelegramAccount)
            .where(TelegramAccount.user_id == user.id)
            .order_by(TelegramAccount.created_at.desc())
        )
        accounts = result.scalars().all()
        return [await AccountService._to_response(acc, db) for acc in accounts]

    @staticmethod
    async def get_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccountResponse:
        """Get specific account"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        return await AccountService._to_response(account, db)

    @staticmethod
    async def start_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccountResponse:
        """Start account monitoring"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

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

        return await AccountService._to_response(account, db)

    @staticmethod
    async def stop_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccountResponse:
        """Stop account monitoring"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        await telegram_manager.stop_client(account_id, db)
        await db.refresh(account)
        return await AccountService._to_response(account, db)

    @staticmethod
    async def delete_account(account_id: int, user: User, db: AsyncSession):
        """Delete account"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        await telegram_manager.delete_client(account, account_id, db)
        await db.execute(delete(TelegramAccount).where(TelegramAccount.id == account_id))
        await db.commit()

    @staticmethod
    async def create_monitoring_task(
            account_id: int,
            task_data: MonitoringTaskCreate,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Create a new monitoring task"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        result = await db.execute(
            select(func.count(MonitoringTask.id)).where(MonitoringTask.account_id == account_id)
        )
        task_count = result.scalar()
        if task_count >= 5:
            raise ValueError("Maximum number of monitoring tasks (5) reached for this account")

        new_task = MonitoringTask(
            account_id=account_id,
            name=task_data.name,
            whitelist_keywords=json.dumps(task_data.whitelist_keywords, ensure_ascii=False),
            blacklist_keywords=json.dumps(task_data.blacklist_keywords, ensure_ascii=False),
            monitored_channels=json.dumps(task_data.monitored_channels, ensure_ascii=False),
            forward_to_chat_id=task_data.forward_to_chat_id,
            replacements=json.dumps(task_data.replacements, ensure_ascii=False),
            is_active=True
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return AccountService._task_to_response(new_task)

    @staticmethod
    async def update_monitoring_task(
            account_id: int,
            task_id: int,
            task_data: MonitoringTaskUpdate,
            user: User,
            db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Update a monitoring task"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        result = await db.execute(
            select(MonitoringTask).where(
                MonitoringTask.id == task_id,
                MonitoringTask.account_id == account_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Monitoring task not found")

        if task_data.name is not None:
            task.name = task_data.name
        if task_data.whitelist_keywords is not None:
            task.whitelist_keywords = json.dumps(task_data.whitelist_keywords, ensure_ascii=False)
        if task_data.blacklist_keywords is not None:
            task.blacklist_keywords = json.dumps(task_data.blacklist_keywords, ensure_ascii=False)
        if task_data.monitored_channels is not None:
            task.monitored_channels = json.dumps(task_data.monitored_channels, ensure_ascii=False)
        if task_data.forward_to_chat_id is not None:
            task.forward_to_chat_id = task_data.forward_to_chat_id
        if task_data.replacements is not None:
            task.replacements = json.dumps(task_data.replacements, ensure_ascii=False)
        if task_data.is_active is not None:
            task.is_active = task_data.is_active

        await db.commit()
        await db.refresh(task)

        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return AccountService._task_to_response(task)

    @staticmethod
    async def start_monitoring_task(account_id: int, task_id: int, user: User, db: AsyncSession) -> MonitoringTaskResponse:
        """Start a monitoring task"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        result = await db.execute(
            select(MonitoringTask).where(
                MonitoringTask.id == task_id,
                MonitoringTask.account_id == account_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Monitoring task not found")

        task.is_active = True
        await db.commit()
        await db.refresh(task)

        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return AccountService._task_to_response(task)

    @staticmethod
    async def stop_monitoring_task(account_id: int, task_id: int, user: User,
                                   db: AsyncSession) -> MonitoringTaskResponse:
        """Stop a monitoring task"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        result = await db.execute(
            select(MonitoringTask).where(
                MonitoringTask.id == task_id,
                MonitoringTask.account_id == account_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Monitoring task not found")

        task.is_active = False
        await db.commit()
        await db.refresh(task)

        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

        return AccountService._task_to_response(task)

    @staticmethod
    async def delete_monitoring_task(account_id: int, task_id: int, user: User, db: AsyncSession):
        """Delete a monitoring task"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        result = await db.execute(
            select(MonitoringTask).where(
                MonitoringTask.id == task_id,
                MonitoringTask.account_id == account_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Monitoring task not found")

        await db.execute(delete(MonitoringTask).where(MonitoringTask.id == task_id))
        await db.commit()

        if account.status == AccountStatus.ACTIVE and account.is_active:
            await telegram_manager.update_monitoring(account_id, db)

    @staticmethod
    def _task_to_response(task: MonitoringTask) -> MonitoringTaskResponse:
        """Convert task to response model"""
        return MonitoringTaskResponse(
            id=task.id,
            account_id=task.account_id,
            name=task.name,
            whitelist_keywords=json.loads(task.whitelist_keywords or "[]"),
            blacklist_keywords=json.loads(task.blacklist_keywords or "[]"),
            monitored_channels=json.loads(task.monitored_channels or "[]"),
            forward_to_chat_id=task.forward_to_chat_id,
            replacements=json.loads(task.replacements or "{}"),
            is_active=task.is_active,
            created_at=task.created_at
        )

    @staticmethod
    async def _to_response(account: TelegramAccount, db: AsyncSession) -> TelegramAccountResponse:
        """Convert account to response model"""
        result = await db.execute(
            select(func.count(AccountNotification.id))
            .where(
                AccountNotification.account_id == account.id,
                AccountNotification.is_read == False
            )
        )
        unread_count = result.scalar() or 0

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
            monitoring_tasks=[AccountService._task_to_response(t) for t in tasks]
        )

    @staticmethod
    async def get_notifications(account_id: int, user: User, db: AsyncSession) -> List[AccountNotificationResponse]:
        """Get account notifications"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Account not found")

        result = await db.execute(
            select(AccountNotification)
            .where(AccountNotification.account_id == account_id)
            .order_by(AccountNotification.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def mark_notification_read(
            account_id: int,
            notification_id: int,
            user: User,
            db: AsyncSession
    ):
        """Mark notification as read"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Account not found")

        result = await db.execute(select(AccountNotification).where(AccountNotification.id == notification_id,
                                                                    AccountNotification.account_id == account_id))
        notification = result.scalar_one_or_none()
        if not notification:
            raise ValueError("Notification not found")

        notification.is_read = True
        await db.commit()