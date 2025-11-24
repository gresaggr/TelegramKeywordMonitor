"""Database operations for Telegram client manager"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logger import get_logger
from app.models.account import TelegramAccount, AccountStatus, AccountNotification

logger = get_logger("telegram.db")


class DatabaseOperations:
    """Handles database operations for Telegram clients"""

    @staticmethod
    async def _get_session():
        """Create a new database session"""
        from app.db.session import engine
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        return async_session()

    async def update_account_status(
            self,
            account_id: int,
            status: AccountStatus,
            error_message: Optional[str] = None,
            is_active: Optional[bool] = None
    ):
        """Update account status in database"""
        values = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if is_active is not None:
            values["is_active"] = is_active

        async with await self._get_session() as session:
            await session.execute(
                update(TelegramAccount)
                .where(TelegramAccount.id == account_id)
                .values(**values)
            )
            await session.commit()

    async def handle_error(
            self,
            account_id: int,
            error_message: str,
            error_type: str
    ):
        """Handle errors by updating status and creating notifications"""
        await self.update_account_status(
            account_id, AccountStatus.ERROR, error_message, is_active=False
        )

        async with await self._get_session() as session:
            notification = AccountNotification(
                account_id=account_id,
                message=error_message,
                error_type=error_type
            )
            session.add(notification)
            await session.commit()

        if settings.TELEGRAM_BOT_TOKEN and settings.ADMIN_TELEGRAM_CHAT_ID:
            await self._send_admin_notification(account_id, error_message, error_type)

        logger.error(f"Error handled for account {account_id}: {error_message}")

    async def _send_admin_notification(
            self,
            account_id: int,
            error_message: str,
            error_type: str
    ):
        """Send error notification to admin"""
        try:
            from app.services.telegram import send_telegram_notification

            # Escape markdown special characters
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            error_safe = error_message
            for char in special_chars:
                error_safe = error_safe.replace(char, f'\\{char}')

            admin_message = (
                f"⚠️ *Telegram Account Error*\n\n"
                f"*Account ID:* {account_id}\n"
                f"*Error Type:* {error_type}\n"
                f"*Message:* {error_safe}\n"
                f"*Time:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            await send_telegram_notification(settings.ADMIN_TELEGRAM_CHAT_ID, admin_message)
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")

    async def get_active_accounts(self) -> list[TelegramAccount]:
        """Get all active accounts from database"""
        async with await self._get_session() as session:
            result = await session.execute(
                select(TelegramAccount).where(
                    TelegramAccount.status == AccountStatus.ACTIVE,
                    TelegramAccount.is_active == True
                )
            )
            return result.scalars().all()

    async def get_account(self, account_id: int) -> Optional[TelegramAccount]:
        """Get account by ID"""
        async with await self._get_session() as session:
            result = await session.execute(
                select(TelegramAccount).where(TelegramAccount.id == account_id)
            )
            return result.scalar_one_or_none()
