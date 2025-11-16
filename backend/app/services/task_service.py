"""Service for monitoring task operations"""
import json
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.account import TelegramAccount, MonitoringTask, AccountStatus
from app.models.user import User
from app.schemas.account import (
    MonitoringTaskCreate,
    MonitoringTaskUpdate,
    MonitoringTaskResponse
)
from app.core.logger import get_logger

logger = get_logger("services.task")


class TaskService:
    """Service for managing monitoring tasks"""

    @staticmethod
    def task_to_response(task: MonitoringTask) -> MonitoringTaskResponse:
        """Convert task model to response schema"""
        return MonitoringTaskResponse(
            id=task.id,
            account_id=task.account_id,
            name=task.name,
            whitelist_keywords=json.loads(task.whitelist_keywords or "[]"),
            blacklist_keywords=json.loads(task.blacklist_keywords or "[]"),
            monitored_channels=json.loads(task.monitored_channels or "[]"),
            forward_to_chat_id=task.forward_to_chat_id,
            replacements=json.loads(task.replacements or "{}"),
            is_active=task.is_active,
            created_at=task.created_at
        )

    async def create_task(
        self,
        account_id: int,
        task_data: MonitoringTaskCreate,
        user: User,
        db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Create a new monitoring task"""
        # Verify account ownership
        account = await self._get_user_account(account_id, user, db)

        # Check task limit
        result = await db.execute(
            select(func.count(MonitoringTask.id))
            .where(MonitoringTask.account_id == account_id)
        )
        task_count = result.scalar()
        if task_count >= 5:
            raise ValueError("Maximum number of monitoring tasks (5) reached")

        # Create task
        new_task = MonitoringTask(
            account_id=account_id,
            name=task_data.name,
            whitelist_keywords=json.dumps(task_data.whitelist_keywords, ensure_ascii=False),
            blacklist_keywords=json.dumps(task_data.blacklist_keywords, ensure_ascii=False),
            monitored_channels=json.dumps(task_data.monitored_channels, ensure_ascii=False),
            forward_to_chat_id=task_data.forward_to_chat_id,
            replacements=json.dumps(task_data.replacements, ensure_ascii=False),
            is_active=True
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        return self.task_to_response(new_task)

    async def update_task(
        self,
        account_id: int,
        task_id: int,
        task_data: MonitoringTaskUpdate,
        user: User,
        db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Update a monitoring task"""
        # Verify account ownership
        await self._get_user_account(account_id, user, db)

        # Get task
        task = await self._get_task(account_id, task_id, db)

        # Update fields
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.whitelist_keywords is not None:
            task.whitelist_keywords = json.dumps(task_data.whitelist_keywords, ensure_ascii=False)
        if task_data.blacklist_keywords is not None:
            task.blacklist_keywords = json.dumps(task_data.blacklist_keywords, ensure_ascii=False)
        if task_data.monitored_channels is not None:
            task.monitored_channels = json.dumps(task_data.monitored_channels, ensure_ascii=False)
        if task_data.forward_to_chat_id is not None:
            task.forward_to_chat_id = task_data.forward_to_chat_id
        if task_data.replacements is not None:
            task.replacements = json.dumps(task_data.replacements, ensure_ascii=False)
        if task_data.is_active is not None:
            task.is_active = task_data.is_active

        await db.commit()
        await db.refresh(task)

        return self.task_to_response(task)

    async def toggle_task_status(
        self,
        account_id: int,
        task_id: int,
        is_active: bool,
        user: User,
        db: AsyncSession
    ) -> MonitoringTaskResponse:
        """Start or stop a monitoring task"""
        await self._get_user_account(account_id, user, db)
        task = await self._get_task(account_id, task_id, db)

        task.is_active = is_active
        await db.commit()
        await db.refresh(task)

        return self.task_to_response(task)

    async def delete_task(
        self,
        account_id: int,
        task_id: int,
        user: User,
        db: AsyncSession
    ):
        """Delete a monitoring task"""
        await self._get_user_account(account_id, user, db)
        await self._get_task(account_id, task_id, db)

        await db.execute(
            delete(MonitoringTask).where(MonitoringTask.id == task_id)
        )
        await db.commit()

    async def _get_user_account(
        self,
        account_id: int,
        user: User,
        db: AsyncSession
    ) -> TelegramAccount:
        """Get account and verify ownership"""
        result = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user.id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        return account

    async def _get_task(
        self,
        account_id: int,
        task_id: int,
        db: AsyncSession
    ) -> MonitoringTask:
        """Get task by ID"""
        result = await db.execute(
            select(MonitoringTask).where(
                MonitoringTask.id == task_id,
                MonitoringTask.account_id == account_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Monitoring task not found")
        return task
