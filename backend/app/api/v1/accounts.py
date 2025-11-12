from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import List
import json

from app.db.session import get_async_session
from app.models.user import User
from app.models.account import TelegramAccount, AccountStatus, AccountNotification
from app.schemas.account import (
    TelegramAccountCreate,
    TelegramAccountUpdate,
    TelegramAccountResponse,
    VerifyCodeRequest,
    AccountNotificationResponse
)
from app.api.deps import get_current_user
from app.telegram.client_manager import telegram_manager
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger("api.accounts")


@router.post("/", response_model=TelegramAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
        account_data: TelegramAccountCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Create a new Telegram account and start authentication"""

    # Create account record
    new_account = TelegramAccount(
        user_id=current_user.id,
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

    # Initialize Telegram client
    try:
        client, needs_auth = await telegram_manager.create_client(new_account, db)

        if needs_auth:
            logger.info(f"Auth code sent for account {new_account.id}")
        else:
            # Already authorized, start monitoring
            await telegram_manager._start_monitoring(new_account.id, db)
            new_account.status = AccountStatus.ACTIVE
            new_account.is_active = True
            await db.commit()

    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    await db.refresh(new_account)
    return await _account_to_response(new_account, db)


@router.post("/verify-code", response_model=TelegramAccountResponse)
async def verify_code(
        verify_data: VerifyCodeRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Verify authentication code and optional 2FA password"""

    # Get account and verify ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == verify_data.account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    try:
        await telegram_manager.verify_code(
            verify_data.account_id,
            verify_data.code,
            verify_data.two_fa_password,
            db
        )

        await db.refresh(account)
        logger.info(f"Account {account.id} successfully authorized")

        return await _account_to_response(account, db)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[TelegramAccountResponse])
async def get_accounts(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get all Telegram accounts for the current user"""

    result = await db.execute(
        select(TelegramAccount).where(TelegramAccount.user_id == current_user.id)
        .order_by(TelegramAccount.created_at.desc())
    )
    accounts = result.scalars().all()

    return [await _account_to_response(acc, db) for acc in accounts]


@router.get("/{account_id}", response_model=TelegramAccountResponse)
async def get_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get a specific Telegram account"""

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return await _account_to_response(account, db)


@router.patch("/{account_id}", response_model=TelegramAccountResponse)
async def update_account(
        account_id: int,
        account_data: TelegramAccountUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Update Telegram account monitoring settings"""

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Update fields
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

    # Update running client if active
    if account.status == AccountStatus.ACTIVE and account.is_active:
        try:
            await telegram_manager.update_client_settings(account_id, db)
        except Exception as e:
            logger.error(f"Error updating client settings: {e}")

    logger.info(f"Account {account_id} updated")
    return await _account_to_response(account, db)


@router.post("/{account_id}/start", response_model=TelegramAccountResponse)
async def start_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Start/resume monitoring for a Telegram account"""

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if account.status == AccountStatus.AWAITING_CODE or account.status == AccountStatus.AWAITING_2FA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete authorization first"
        )

    try:
        # Check if client exists and is authorized
        client = telegram_manager.clients.get(account_id)
        if not client:
            # Try to reconnect
            client, needs_auth = await telegram_manager.create_client(account, db)
            if needs_auth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Authorization required"
                )

        # Start monitoring
        await telegram_manager._start_monitoring(account_id, db)
        await db.refresh(account)

        logger.info(f"Account {account_id} started")
        return await _account_to_response(account, db)

    except Exception as e:
        logger.error(f"Error starting account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{account_id}/stop", response_model=TelegramAccountResponse)
async def stop_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Stop monitoring for a Telegram account"""

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    await telegram_manager.stop_client(account_id, db)
    await db.refresh(account)

    logger.info(f"Account {account_id} stopped")
    return await _account_to_response(account, db)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Delete a Telegram account"""

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Stop and delete client
    await telegram_manager.delete_client(account_id, db)

    # Delete from database
    await db.execute(
        delete(TelegramAccount).where(TelegramAccount.id == account_id)
    )
    await db.commit()

    logger.info(f"Account {account_id} deleted")


@router.get("/{account_id}/notifications", response_model=List[AccountNotificationResponse])
async def get_notifications(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get notifications for an account"""

    # Verify account ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Get notifications
    result = await db.execute(
        select(AccountNotification)
        .where(AccountNotification.account_id == account_id)
        .order_by(AccountNotification.created_at.desc())
    )
    notifications = result.scalars().all()

    return notifications


@router.post("/{account_id}/notifications/{notification_id}/read")
async def mark_notification_read(
        account_id: int,
        notification_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Mark a notification as read"""

    # Verify account ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Update notification
    result = await db.execute(
        select(AccountNotification).where(
            AccountNotification.id == notification_id,
            AccountNotification.account_id == account_id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    await db.commit()

    return {"status": "ok"}


async def _account_to_response(account: TelegramAccount, db: AsyncSession) -> TelegramAccountResponse:
    """Convert account model to response schema"""

    # Count unread notifications
    result = await db.execute(
        select(func.count(AccountNotification.id))
        .where(
            AccountNotification.account_id == account.id,
            AccountNotification.is_read == False
        )
    )
    unread_count = result.scalar() or 0

    return TelegramAccountResponse(
        id=account.id,
        phone_number=account.phone_number,
        status=account.status,
        is_active=account.is_active,
        whitelist_keywords=json.loads(account.whitelist_keywords or "[]"),
        blacklist_keywords=json.loads(account.blacklist_keywords or "[]"),
        monitored_channels=json.loads(account.monitored_channels or "[]"),
        forward_to_chat_id=account.forward_to_chat_id,
        replacements=json.loads(account.replacements or "{}"),
        error_message=account.error_message,
        unread_notifications_count=unread_count,
        created_at=account.created_at,
        last_activity=account.last_activity
    )
