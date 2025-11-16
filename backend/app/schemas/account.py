from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.account import AccountStatus


class ProxySettings(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None


class MonitoringTaskBase(BaseModel):
    name: str
    whitelist_keywords: List[str] = Field(default_factory=list)
    blacklist_keywords: List[str] = Field(default_factory=list)
    monitored_channels: List[str] = Field(default_factory=list)
    forward_to_chat_id: str
    replacements: Dict[str, str] = Field(default_factory=dict)


class MonitoringTaskCreate(MonitoringTaskBase):
    pass


class MonitoringTaskUpdate(BaseModel):
    name: Optional[str] = None
    whitelist_keywords: Optional[List[str]] = None
    blacklist_keywords: Optional[List[str]] = None
    monitored_channels: Optional[List[str]] = None
    forward_to_chat_id: Optional[str] = None
    replacements: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class MonitoringTaskResponse(BaseModel):
    id: int
    account_id: int
    name: str
    whitelist_keywords: List[str]
    blacklist_keywords: List[str]
    monitored_channels: List[str]
    forward_to_chat_id: str
    replacements: Dict[str, str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramAccountBase(BaseModel):
    phone_number: str
    api_id: str
    api_hash: str
    device_model: Optional[str] = "PC"
    system_version: Optional[str] = "Linux"
    app_version: Optional[str] = "1.0.0"
    proxy: Optional[ProxySettings] = None
    name: Optional[str] = None


class TelegramAccountCreate(TelegramAccountBase):
    pass


class TelegramAccountUpdate(BaseModel):
    name: Optional[str] = None
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    device_model: Optional[str] = None
    system_version: Optional[str] = None
    app_version: Optional[str] = None
    proxy: Optional[ProxySettings] = None


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
    name: Optional[str]
    status: AccountStatus
    is_active: bool
    error_message: Optional[str]
    unread_notifications_count: int = 0
    created_at: datetime
    last_activity: Optional[datetime]
    monitoring_tasks: List[MonitoringTaskResponse] = []

    class Config:
        from_attributes = True


class VerifyCodeRequest(BaseModel):
    account_id: int
    code: str
    two_fa_password: Optional[str] = None