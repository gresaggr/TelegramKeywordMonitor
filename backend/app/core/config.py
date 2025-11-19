from pathlib import Path
from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Telegram Keyword Monitor"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Redis for Celery and message queue
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Telegram Bot for admin notifications
    TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_CHAT_ID: str = ""

    # Telegram sessions directory
    SESSIONS_DIR: str = "/app/backend/sessions"

    # Monitoring defaults
    DEFAULT_CHECK_INTERVAL: int = 300
    DEFAULT_TIMEOUT: int = 30
    MAX_CONCURRENT_CHECKS: int = 100
    ACCOUNT_HEALTH_CHECK_INTERVAL: int = 300  # 5 minutes проверять валидность аккаунтов

    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Billing settings
    MONTHLY_COST_MAX: float = 1000.0
    BALANCE_CHECK_INTERVAL: int = 600  # 10 minutes in seconds
    START_BALANCE: int = 10  # 10 руб стартового баланса при регистрации

    MAXIMUM_NUMBER_OF_ACCOUNTS: int = 5  # сколько максимум ТГ аккаунтов на одном аккаунте
    MAXIMUM_NUMBER_OF_TASKS: int = 5  # сколько максимум тасок на одном ТГ аккаунте
    MAXIMUM_NUMBER_OF_CHANNELS: int = 5  # сколько максимум каналов в одной таске

    # Task limits
    MAX_KEYWORD_LINES: int = 10  # максимум строк в белом/черном списке
    MAX_KEYWORD_LENGTH: int = 50  # максимум символов в одной строке ключевого слова
    MAX_REPLACEMENT_LINES: int = 10  # максимум строк замен
    MAX_REPLACEMENT_LENGTH: int = 50  # максимум символов в одной строке замены

    # YooKassa payment settings
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    YOOKASSA_RETURN_URL: str = "http://localhost:8080"
    YOOKASSA_WEBHOOK_URL: str = ""

    env_path: ClassVar[str] = str(Path(__file__).parent.parent.parent.parent / ".env")
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()