"""Combined router for accounts, tasks, and notifications"""
from fastapi import APIRouter

from .endpoints import accounts, tasks, notifications

router = APIRouter()


router.include_router(accounts.router, tags=["Accounts"])


router.include_router(tasks.router, tags=["Tasks"])


router.include_router(notifications.router, tags=["Notifications"])
