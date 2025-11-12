from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.account import AccountStatus


class ProxySettings(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None


class TelegramAccountBase(BaseModel):
    phone_number: str
    api_id: str
    api_hash: str
    device_model: Optional[str] = "PC"
    system_version: Optional[str] = "Linux"
    app_version: Optional[str] = "1.0.0"
    proxy: Optional[ProxySettings] = None
    whitelist_keywords: List[str] = Field(default_factory=list)
    blacklist_keywords: List[str] = Field(default_factory=list)
    monitored_channels: List[str] = Field(default_factory=list)
    forward_to_chat_id: Optional[str] = None
    replacements: Dict[str, str] = Field(default_factory=dict)


class TelegramAccountCreate(TelegramAccountBase):
    pass


class TelegramAccountUpdate(BaseModel):
    whitelist_keywords: Optional[List[str]] = None
    blacklist_keywords: Optional[List[str]] = None
    monitored_channels: Optional[List[str]] = None
    forward_to_chat_id: Optional[str] = None
    replacements: Optional[Dict[str, str]] = None


class AccountNotificationResponse(BaseModel):
    id: int
    message: str
    error_type: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramAccountResponse(BaseModel):
    id: int
    phone_number: str
    status: AccountStatus
    is_active: bool
    whitelist_keywords: List[str]
    blacklist_keywords: List[str]
    monitored_channels: List[str]
    forward_to_chat_id: Optional[str]
    replacements: Dict[str, str]
    error_message: Optional[str]
    unread_notifications_count: int = 0
    created_at: datetime
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True


class VerifyCodeRequest(BaseModel):
    account_id: int
    code: str
    two_fa_password: Optional[str] = None


class StartAccountRequest(BaseModel):
    account_id: int


class StopAccountRequest(BaseModel):
    account_id: int
