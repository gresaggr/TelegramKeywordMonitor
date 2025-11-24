from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_async_session
from app.models.user import User
from app.api.deps import get_current_user
from app.services.billing_service import billing_service

router = APIRouter()


class BalanceResponse(BaseModel):
    balance: float
    active_accounts: int
    active_tasks: int
    hourly_cost: float


class TopUpRequest(BaseModel):
    amount: float


@router.get("/", response_model=BalanceResponse)
async def get_balance(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Get current user balance and billing info"""
    active_accounts, active_tasks = await billing_service.get_user_active_stats(
        current_user.id, db
    )
    hourly_cost = billing_service.calculate_hourly_cost(active_accounts, active_tasks)

    return BalanceResponse(
        balance=current_user.balance,
        active_accounts=active_accounts,
        active_tasks=active_tasks,
        hourly_cost=hourly_cost
    )


@router.post("/topup", response_model=BalanceResponse)
async def topup_balance(
        topup_data: TopUpRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Top up balance (stub - payment integration needed)"""
    # TODO: сделать оплату через ЮКассу

    current_user.balance += topup_data.amount
    await db.commit()
    await db.refresh(current_user)

    active_accounts, active_tasks = await billing_service.get_user_active_stats(
        current_user.id, db
    )
    hourly_cost = billing_service.calculate_hourly_cost(active_accounts, active_tasks)

    return BalanceResponse(
        balance=current_user.balance,
        active_accounts=active_accounts,
        active_tasks=active_tasks,
        hourly_cost=hourly_cost
    )