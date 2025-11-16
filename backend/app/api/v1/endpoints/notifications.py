"""Notification endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_session
from app.models.user import User
from app.schemas.account import AccountNotificationResponse
from app.api.deps import get_current_user
from app.services.account_service import AccountService
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger("api.notifications")


@router.get("/{account_id}/notifications", response_model=List[AccountNotificationResponse])
async def get_notifications(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get notifications for an account"""
    try:
        return await AccountService.get_notifications(account_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{account_id}/notifications/{notification_id}/read")
async def mark_notification_read(
    account_id: int,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Mark a notification as read"""
    try:
        await AccountService.mark_notification_read(account_id, notification_id, current_user, db)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
