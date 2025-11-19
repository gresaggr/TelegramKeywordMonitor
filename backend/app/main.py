# backend/app/main.py
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logger import logger
from app.api.v1 import auth, balance, accounts, payments
from app.telegram.client_manager import telegram_manager
from app.db.session import async_session_maker
from app.services.billing_service import billing_service

limiter = Limiter(key_func=get_remote_address)


async def billing_loop():
    """Background task for processing billing"""
    logger.info(f"Billing loop started (interval: {settings.BALANCE_CHECK_INTERVAL}s)")

    while True:
        try:
            await asyncio.sleep(settings.BALANCE_CHECK_INTERVAL)
            await billing_service.process_all_users()
        except Exception as e:
            logger.error(f"Error in billing loop: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} is starting up...")
    logger.info(f"📊 Database: {settings.DATABASE_URL.split('@')[1]}")
    logger.info(f"📮 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"📁 Sessions: {settings.SESSIONS_DIR}")
    logger.info(f"💰 Billing: ${settings.MONTHLY_COST_MAX}/month, check every {settings.BALANCE_CHECK_INTERVAL}s")
    if settings.TELEGRAM_BOT_TOKEN:
        logger.info("🔔 Telegram Bot: ✓ Configured")
    else:
        logger.info("🔔 Telegram Bot: ✗ Not configured")
    if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
        logger.info("💳 YooKassa: ✓ Configured")
    else:
        logger.info("💳 YooKassa: ✗ Not configured")
    logger.info("=" * 60)

    # Restore active accounts with concurrency limit
    async with async_session_maker() as db:
        await telegram_manager.startup_restore_accounts(db)

    # Start billing background task
    billing_task = asyncio.create_task(billing_loop())

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Application shutting down...")

    # Cancel billing task
    billing_task.cancel()
    try:
        await billing_task
    except asyncio.CancelledError:
        pass

    # Shutdown all accounts
    await telegram_manager.shutdown_all_accounts()
    logger.info("=" * 60)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Асинхронный сервис мониторинга ключевых слов в Telegram чатах",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    balance.router,
    prefix=f"{settings.API_V1_PREFIX}/balance",
    tags=["Balance"]
)

app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["Telegram Accounts"]
)

app.include_router(
    payments.router,
    prefix=f"{settings.API_V1_PREFIX}/payments",
    tags=["Payments"]
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Telegram keyword monitoring",
            "Multiple accounts support",
            "Keyword filtering (whitelist/blacklist)",
            "Message forwarding with replacements",
            "Real-time notifications",
            "User dashboard",
            "Automated billing (channel-based pricing)",
            "YooKassa payment integration"
        ]
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
