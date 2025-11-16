"""Payment endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_session
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentWebhook
from app.api.deps import get_current_user
from app.services.yookassa_service import yookassa_service
from app.core.logger import get_logger
from sqlalchemy import select
from app.models.payment import Payment

router = APIRouter()
logger = get_logger("api.payments")


@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
        payment_data: PaymentCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new payment for balance top-up

    Returns payment object with confirmation_url for redirect
    """
    try:
        payment = await yookassa_service.create_payment(
            user_id=current_user.id,
            amount=payment_data.amount,
            description=payment_data.description or f"Balance top-up for user {current_user.username}",
            db=db
        )
        return payment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/webhook")
async def payment_webhook(
        request: Request,
        db: AsyncSession = Depends(get_async_session)
):
    """
    Webhook endpoint for YooKassa payment notifications

    This endpoint should be publicly accessible and configured in YooKassa dashboard
    """
    try:
        webhook_data = await request.json()
        logger.info(f"Received webhook: {webhook_data.get('event')}")

        payment = await yookassa_service.process_webhook(webhook_data, db)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook"
            )

        return {"status": "ok", "payment_id": payment.id}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get payment history for current user"""
    try:
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()
        return payments
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
        payment_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get specific payment details"""
    try:
        result = await db.execute(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.user_id == current_user.id
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        return payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{yookassa_payment_id}/check", response_model=PaymentResponse)
async def check_payment_status(
        yookassa_payment_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """
    Manually check payment status from YooKassa

    Useful for checking payment after redirect from payment page
    """
    try:
        # Verify payment belongs to current user
        result = await db.execute(
            select(Payment).where(
                Payment.yookassa_payment_id == yookassa_payment_id,
                Payment.user_id == current_user.id
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        # Update payment status from YooKassa
        updated_payment = await yookassa_service.get_payment_status(yookassa_payment_id, db)

        if not updated_payment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check payment status"
            )

        return updated_payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
