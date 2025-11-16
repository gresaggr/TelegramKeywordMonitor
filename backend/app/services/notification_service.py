"""Service for account notification operations"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.account import TelegramAccount, AccountNotification
from app.models.user import User
from app.schemas.account import AccountNotificationResponse
from app.core.logger import get_logger

logger = get_logger("services.notification")


class NotificationService:
    """Service for managing account notifications"""

    async def get_notifications(
        self,
        account_id: int,
        user: User,
        db: AsyncSession
    ) -> List[AccountNotificationResponse]:
        """Get all notifications for an account"""
        # Verify account ownership
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Account not found")

        # Get notifications
        result = await db.execute(
            select(AccountNotification)
            .where(AccountNotification.account_id == account_id)
            .order_by(AccountNotification.created_at.desc())
        )
        return result.scalars().all()

    async def mark_notification_read(
        self,
        account_id: int,
        notification_id: int,
        user: User,
        db: AsyncSession
    ):
        """Mark a notification as read"""
        # Verify account ownership
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Account not found")

        # Get and update notification
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
