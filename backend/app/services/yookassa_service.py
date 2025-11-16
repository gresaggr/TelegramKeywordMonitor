"""YooKassa payment service"""
import uuid
from typing import Optional
from datetime import datetime, timezone

from yookassa import Configuration, Payment as YooKassaPayment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logger import get_logger
from app.models.payment import Payment, PaymentStatus
from app.models.user import User

logger = get_logger("services.yookassa")

# Configure YooKassa
if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    logger.info("YooKassa configured successfully")
else:
    logger.warning("YooKassa credentials not configured")


class YooKassaService:
    """Service for YooKassa payment processing"""

    @staticmethod
    async def create_payment(
            user_id: int,
            amount: float,
            description: str,
            db: AsyncSession
    ) -> Payment:
        """
        Create a new payment in YooKassa and database

        Args:
            user_id: User ID
            amount: Payment amount in RUB
            description: Payment description
            db: Database session

        Returns:
            Payment object with confirmation URL
        """
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            raise ValueError("YooKassa is not configured. Please set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY")

        try:
            # Create payment in YooKassa
            idempotence_key = str(uuid.uuid4())

            yookassa_payment = YooKassaPayment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.YOOKASSA_RETURN_URL
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": str(user_id)
                }
            }, idempotence_key)

            # Save payment to database
            payment = Payment(
                user_id=user_id,
                yookassa_payment_id=yookassa_payment.id,
                amount=amount,
                currency="RUB",
                status=PaymentStatus.PENDING,
                description=description,
                confirmation_url=yookassa_payment.confirmation.confirmation_url
            )

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            logger.info(f"Payment created: {payment.id} for user {user_id}, amount: {amount} RUB")
            return payment

        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise

    @staticmethod
    async def process_webhook(
            webhook_data: dict,
            db: AsyncSession
    ) -> Optional[Payment]:
        """
        Process webhook notification from YooKassa

        Args:
            webhook_data: Webhook data from YooKassa
            db: Database session

        Returns:
            Updated Payment object or None
        """
        try:
            event = webhook_data.get("event")
            payment_data = webhook_data.get("object", {})
            yookassa_payment_id = payment_data.get("id")

            if not yookassa_payment_id:
                logger.error("No payment ID in webhook data")
                return None

            # Get payment from database
            result = await db.execute(
                select(Payment).where(Payment.yookassa_payment_id == yookassa_payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment not found: {yookassa_payment_id}")
                return None

            # Update payment status
            old_status = payment.status
            new_status = payment_data.get("status")

            if event == "payment.succeeded" and new_status == "succeeded":
                payment.status = PaymentStatus.SUCCEEDED
                payment.paid_at = datetime.now(timezone.utc)

                # Get payment method
                payment_method_data = payment_data.get("payment_method", {})
                payment.payment_method = payment_method_data.get("type", "unknown")

                # Add balance to user
                result = await db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    user.balance += payment.amount
                    logger.info(
                        f"Payment {payment.id} succeeded. "
                        f"Added {payment.amount} RUB to user {user.id}. "
                        f"New balance: {user.balance}"
                    )

                    # Send notification if configured
                    if user.default_telegram_chat_id:
                        await YooKassaService._send_payment_notification(user, payment)

            elif event == "payment.canceled" or new_status == "canceled":
                payment.status = PaymentStatus.CANCELED
                logger.info(f"Payment {payment.id} canceled")

            elif new_status == "failed":
                payment.status = PaymentStatus.FAILED
                logger.info(f"Payment {payment.id} failed")

            await db.commit()
            await db.refresh(payment)

            logger.info(f"Payment {payment.id} status updated: {old_status} -> {payment.status}")
            return payment

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            await db.rollback()
            return None

    @staticmethod
    async def get_payment_status(
            payment_id: str,
            db: AsyncSession
    ) -> Optional[Payment]:
        """
        Get payment status from YooKassa and update database

        Args:
            payment_id: YooKassa payment ID
            db: Database session

        Returns:
            Updated Payment object or None
        """
        try:
            # Get payment from YooKassa
            yookassa_payment = YooKassaPayment.find_one(payment_id)

            # Get payment from database
            result = await db.execute(
                select(Payment).where(Payment.yookassa_payment_id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment not found in database: {payment_id}")
                return None

            # Update status if changed
            yookassa_status = yookassa_payment.status
            if yookassa_status == "succeeded" and payment.status != PaymentStatus.SUCCEEDED:
                payment.status = PaymentStatus.SUCCEEDED
                payment.paid_at = datetime.now(timezone.utc)

                # Add balance to user
                result = await db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.balance += payment.amount
                    logger.info(f"Balance updated for user {user.id}: +{payment.amount} RUB")

            elif yookassa_status == "canceled":
                payment.status = PaymentStatus.CANCELED
            elif yookassa_status == "failed":
                payment.status = PaymentStatus.FAILED

            await db.commit()
            await db.refresh(payment)

            return payment

        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None

    @staticmethod
    async def _send_payment_notification(user: User, payment: Payment):
        """Send payment success notification to user"""
        try:
            from app.services.telegram import send_telegram_notification

            message = (
                f"✅ *Payment Successful*\n\n"
                f"Amount: {payment.amount:.2f} RUB\n"
                f"Payment ID: {payment.yookassa_payment_id}\n"
                f"New Balance: {user.balance:.2f} RUB\n\n"
                f"Thank you for your payment!"
            )

            await send_telegram_notification(user.default_telegram_chat_id, message)
        except Exception as e:
            logger.error(f"Failed to send payment notification: {e}")


# Singleton instance
yookassa_service = YooKassaService()
