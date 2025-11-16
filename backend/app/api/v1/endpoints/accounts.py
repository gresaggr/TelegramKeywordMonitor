"""Account management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_session
from app.models.user import User
from app.schemas.account import (
    TelegramAccountCreate,
    TelegramAccountUpdate,
    TelegramAccountResponse,
    VerifyCodeRequest
)
from app.api.deps import get_current_user
from app.services.account_service import AccountService
from app.core.logger import get_logger
from sqlalchemy import select, func
from app.models.account import TelegramAccount

router = APIRouter()
logger = get_logger("api.accounts")


@router.post("/", response_model=TelegramAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
        account_data: TelegramAccountCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Create a new Telegram account"""
    try:
        # Check account limit
        result = await db.execute(
            select(func.count(TelegramAccount.id))
            .where(TelegramAccount.user_id == current_user.id)
        )
        account_count = result.scalar()

        if account_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of accounts (5) reached."
            )

        account = await AccountService.create_account(account_data, current_user, db)
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-code", response_model=TelegramAccountResponse)
async def verify_code(
        verify_data: VerifyCodeRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Verify authentication code and optional 2FA password"""
    try:
        account = await AccountService.verify_code(
            verify_data.account_id,
            verify_data.code,
            verify_data.two_fa_password,
            current_user,
            db
        )
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[TelegramAccountResponse])
async def get_accounts(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get all Telegram accounts for the current user"""
    return await AccountService.get_accounts(current_user, db)


@router.get("/{account_id}", response_model=TelegramAccountResponse)
async def get_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get a specific Telegram account"""
    try:
        return await AccountService.get_account(account_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{account_id}", response_model=TelegramAccountResponse)
async def update_account(
        account_id: int,
        account_data: TelegramAccountUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Update a Telegram account"""
    try:
        return await AccountService.update_account(account_id, account_data, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{account_id}/start", response_model=TelegramAccountResponse)
async def start_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Start/resume monitoring for a Telegram account"""
    try:
        return await AccountService.start_account(account_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{account_id}/stop", response_model=TelegramAccountResponse)
async def stop_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Stop monitoring for a Telegram account"""
    try:
        return await AccountService.stop_account(account_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
        account_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Delete a Telegram account"""
    try:
        await AccountService.delete_account(account_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
