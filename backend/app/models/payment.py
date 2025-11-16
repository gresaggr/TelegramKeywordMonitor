from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.db.session import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # YooKassa payment info
    yookassa_payment_id = Column(String, unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="RUB", nullable=False)
    status = Column(String, default=PaymentStatus.PENDING, nullable=False)

    # Additional info
    description = Column(Text, nullable=True)
    confirmation_url = Column(Text, nullable=True)
    payment_method = Column(String, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="payments")
