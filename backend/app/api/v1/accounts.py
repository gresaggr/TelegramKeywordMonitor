"""Combined router for accounts, tasks, and notifications"""
from fastapi import APIRouter

from .endpoints import accounts, tasks, notifications

router = APIRouter()

# Include account endpoints
router.include_router(accounts.router, tags=["Accounts"])

# Include task endpoints
router.include_router(tasks.router, tags=["Tasks"])

# Include notification endpoints
router.include_router(notifications.router, tags=["Notifications"])
