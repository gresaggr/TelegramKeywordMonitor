"""Monitoring task endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.account import (
    MonitoringTaskCreate,
    MonitoringTaskUpdate,
    MonitoringTaskResponse
)
from app.api.deps import get_current_user
from app.services.account_service import AccountService
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger("api.tasks")


@router.post("/{account_id}/tasks", response_model=MonitoringTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_monitoring_task(
        account_id: int,
        task_data: MonitoringTaskCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Create a new monitoring task for an account"""
    try:
        if len(task_data.monitored_channels) > settings.MAXIMUM_NUMBER_OF_CHANNELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of monitored channels is {settings.MAXIMUM_NUMBER_OF_CHANNELS}"
            )

        return await AccountService.create_monitoring_task(account_id, task_data, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{account_id}/tasks/{task_id}", response_model=MonitoringTaskResponse)
async def update_monitoring_task(
        account_id: int,
        task_id: int,
        task_data: MonitoringTaskUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Update a monitoring task"""
    try:
        if task_data.monitored_channels is not None and len(task_data.monitored_channels) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of monitored channels is 5"
            )

        return await AccountService.update_monitoring_task(account_id, task_id, task_data, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{account_id}/tasks/{task_id}/start", response_model=MonitoringTaskResponse)
async def start_monitoring_task(
        account_id: int,
        task_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Start a monitoring task"""
    try:
        return await AccountService.start_monitoring_task(account_id, task_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{account_id}/tasks/{task_id}/stop", response_model=MonitoringTaskResponse)
async def stop_monitoring_task(
        account_id: int,
        task_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Stop a monitoring task"""
    try:
        return await AccountService.stop_monitoring_task(account_id, task_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{account_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_task(
        account_id: int,
        task_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Delete a monitoring task"""
    try:
        await AccountService.delete_monitoring_task(account_id, task_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
