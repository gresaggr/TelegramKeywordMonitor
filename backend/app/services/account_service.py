import json
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.account import TelegramAccount, AccountStatus, AccountNotification
from app.models.user import User
from app.schemas.account import TelegramAccountCreate, TelegramAccountUpdate
from app.telegram.client_manager import telegram_manager
from app.core.logger import get_logger

logger = get_logger("services.account")


class AccountService:
    @staticmethod
    async def create_account(
            account_data: TelegramAccountCreate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccount:
        """Create a new Telegram account"""

        # Check if phone number already exists for this user
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
            api_id=account_data.api_id,
            api_hash=account_data.api_hash,
            device_model=account_data.device_model,
            system_version=account_data.system_version,
            app_version=account_data.app_version,
            proxy_host=account_data.proxy.host if account_data.proxy else None,
            proxy_port=account_data.proxy.port if account_data.proxy else None,
            proxy_username=account_data.proxy.username if account_data.proxy else None,
            proxy_password=account_data.proxy.password if account_data.proxy else None,
            whitelist_keywords=json.dumps(account_data.whitelist_keywords, ensure_ascii=False),
            blacklist_keywords=json.dumps(account_data.blacklist_keywords, ensure_ascii=False),
            monitored_channels=json.dumps(account_data.monitored_channels, ensure_ascii=False),
            forward_to_chat_id=account_data.forward_to_chat_id,
            replacements=json.dumps(account_data.replacements, ensure_ascii=False),
            status=AccountStatus.INITIALIZING
        )

        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)

        try:
            client, needs_auth = await telegram_manager.create_client(new_account, db)

            if not needs_auth:
                await telegram_manager._start_monitoring(new_account.id, db)
                new_account.status = AccountStatus.ACTIVE
                new_account.is_active = True
                await db.commit()

            await db.refresh(new_account)
            return new_account

        except Exception as e:
            logger.error(f"Error creating account: {e}")
            new_account.status = AccountStatus.ERROR
            new_account.error_message = str(e)
            await db.commit()
            raise

    @staticmethod
    async def verify_code(
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            user: User,
            db: AsyncSession
    ) -> TelegramAccount:
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
        return account

    @staticmethod
    async def get_accounts(user: User, db: AsyncSession) -> List[TelegramAccount]:
        """Get all accounts for user"""
        result = await db.execute(
            select(TelegramAccount)
            .where(TelegramAccount.user_id == user.id)
            .order_by(TelegramAccount.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccount:
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
        return account

    @staticmethod
    async def update_account(
            account_id: int,
            account_data: TelegramAccountUpdate,
            user: User,
            db: AsyncSession
    ) -> TelegramAccount:
        """Update account settings"""
        account = await AccountService.get_account(account_id, user, db)

        if account_data.whitelist_keywords is not None:
            account.whitelist_keywords = json.dumps(account_data.whitelist_keywords, ensure_ascii=False)
        if account_data.blacklist_keywords is not None:
            account.blacklist_keywords = json.dumps(account_data.blacklist_keywords, ensure_ascii=False)
        if account_data.monitored_channels is not None:
            account.monitored_channels = json.dumps(account_data.monitored_channels, ensure_ascii=False)
        if account_data.forward_to_chat_id is not None:
            account.forward_to_chat_id = account_data.forward_to_chat_id
        if account_data.replacements is not None:
            account.replacements = json.dumps(account_data.replacements, ensure_ascii=False)

        await db.commit()
        await db.refresh(account)

        if account.status == AccountStatus.ACTIVE and account.is_active:
            try:
                await telegram_manager.update_client_settings(account_id, db)
            except Exception as e:
                logger.error(f"Error updating client settings: {e}")

        return account

    @staticmethod
    async def start_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccount:
        """Start account monitoring"""
        account = await AccountService.get_account(account_id, user, db)

        if account.status in [AccountStatus.AWAITING_CODE, AccountStatus.AWAITING_2FA]:
            raise ValueError("Please complete authorization first")

        client = telegram_manager.clients.get(account_id)
        if not client:
            client, needs_auth = await telegram_manager.create_client(account, db)
            if needs_auth:
                raise ValueError("Authorization required")

        await telegram_manager._start_monitoring(account_id, db)

        # Clear error message on successful start
        account.error_message = None
        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def stop_account(account_id: int, user: User, db: AsyncSession) -> TelegramAccount:
        """Stop account monitoring"""
        account = await AccountService.get_account(account_id, user, db)
        await telegram_manager.stop_client(account_id, db)
        await db.refresh(account)
        return account

    @staticmethod
    async def delete_account(account_id: int, user: User, db: AsyncSession):
        """Delete account"""
        account = await AccountService.get_account(account_id, user, db)
        await telegram_manager.delete_client(account_id, db)
        await db.execute(delete(TelegramAccount).where(TelegramAccount.id == account_id))
        await db.commit()

    @staticmethod
    async def get_account_with_notification_count(
            account: TelegramAccount,
            db: AsyncSession
    ) -> dict:
        """Get account data with unread notification count"""
        result = await db.execute(
            select(func.count(AccountNotification.id))
            .where(
                AccountNotification.account_id == account.id,
                AccountNotification.is_read == False
            )
        )
        unread_count = result.scalar() or 0

        return {
            "id": account.id,
            "phone_number": account.phone_number,
            "status": account.status,
            "is_active": account.is_active,
            "whitelist_keywords": json.loads(account.whitelist_keywords or "[]"),
            "blacklist_keywords": json.loads(account.blacklist_keywords or "[]"),
            "monitored_channels": json.loads(account.monitored_channels or "[]"),
            "forward_to_chat_id": account.forward_to_chat_id,
            "replacements": json.loads(account.replacements or "{}"),
            "error_message": account.error_message,
            "unread_notifications_count": unread_count,
            "created_at": account.created_at,
            "last_activity": account.last_activity
        }

    @staticmethod
    async def get_notifications(account_id: int, user: User, db: AsyncSession) -> List[AccountNotification]:
        """Get account notifications"""
        await AccountService.get_account(account_id, user, db)

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
        await AccountService.get_account(account_id, user, db)

        result = await db.execute(
            select(AccountNotification).where(
                AccountNotification.id == notification_id,
                AccountNotification.account_id == account_id
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise ValueError("Notification not found")

        notification.is_read = True
        await db.commit()
