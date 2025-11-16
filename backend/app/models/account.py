from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.db.session import Base


class AccountStatus(str, Enum):
    INITIALIZING = "initializing"
    AWAITING_CODE = "awaiting_code"
    AWAITING_2FA = "awaiting_2fa"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Authentication
    phone_number = Column(String, nullable=False)
    name = Column(String, nullable=True)
    api_id = Column(String, nullable=False)
    api_hash = Column(String, nullable=False)
    phone_code_hash = Column(String, nullable=True)

    # Device info
    device_model = Column(String, nullable=True)
    system_version = Column(String, nullable=True)
    app_version = Column(String, nullable=True)

    # Proxy settings
    proxy_host = Column(String, nullable=True)
    proxy_port = Column(Integer, nullable=True)
    proxy_username = Column(String, nullable=True)
    proxy_password = Column(String, nullable=True)

    # Status
    status = Column(String, default=AccountStatus.INITIALIZING)
    is_active = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="telegram_accounts")
    monitoring_tasks = relationship("MonitoringTask", back_populates="account", cascade="all, delete-orphan")
    notifications = relationship("AccountNotification", back_populates="account", cascade="all, delete-orphan")


class MonitoringTask(Base):
    __tablename__ = "monitoring_tasks"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("telegram_accounts.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    whitelist_keywords = Column(Text, nullable=True)
    blacklist_keywords = Column(Text, nullable=True)
    monitored_channels = Column(Text, nullable=False)
    forward_to_chat_id = Column(String, nullable=False)
    replacements = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("TelegramAccount", back_populates="monitoring_tasks")


class AccountNotification(Base):
    __tablename__ = "account_notifications"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("telegram_accounts.id", ondelete="CASCADE"), nullable=False)

    message = Column(Text, nullable=False)
    error_type = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("TelegramAccount", back_populates="notifications")