import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import logger
from app.api.v1 import auth, balance, accounts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} is starting up...")
    logger.info(f"📊 Database: {settings.DATABASE_URL.split('@')[1]}")
    logger.info(f"📮 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"📁 Sessions: {settings.SESSIONS_DIR}")
    logger.info(f"🔔 Telegram Bot: {'✓ Configured' if settings.TELEGRAM_BOT_TOKEN else '✗ Not configured'}")
    logger.info("=" * 60)
    yield
    logger.info("=" * 60)
    logger.info("🛑 Application shutting down...")
    logger.info("=" * 60)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Асинхронный сервис мониторинга ключевых слов в Telegram чатах",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production настроить конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
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
            "User dashboard"
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