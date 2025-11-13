from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    default_telegram_chat_id = Column(String, nullable=True)
    admin_notification_chat_id = Column(String, nullable=True)

    # Default Telegram account settings
    default_api_id = Column(String, nullable=True, default="2040")
    default_api_hash = Column(String, nullable=True, default="b18441a1ff607e10a989891a5462e627")
    default_device_model = Column(String, nullable=True, default="MS-7C75")
    default_system_version = Column(String, nullable=True, default="Windows 10")
    default_app_version = Column(String, nullable=True, default="4.8.3")
    default_forward_to_chat_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    telegram_accounts = relationship("TelegramAccount", back_populates="user", cascade="all, delete-orphan")
