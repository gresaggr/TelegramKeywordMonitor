from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in RUB")
    description: Optional[str] = "Balance top-up"


class PaymentResponse(BaseModel):
    id: int
    yookassa_payment_id: str
    amount: float
    currency: str
    status: str
    confirmation_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentWebhook(BaseModel):
    """Webhook notification from YooKassa"""
    type: str
    event: str
    object: dict
