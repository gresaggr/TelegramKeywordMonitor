# backend/app/telegram/client_manager.py
"""Manages multiple Telegram client instances"""
import asyncio
from pathlib import Path
from typing import Dict, Optional

from pyrogram import Client
from pyrogram.errors import FloodWait

from app.core.config import settings
from app.core.logger import get_logger
from app.models.account import TelegramAccount, AccountStatus, MonitoringTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .client_factory import ClientFactory
from .auth_handler import AuthHandler
from .monitoring_handler import MonitoringHandler
from .db_operations import DatabaseOperations

logger = get_logger("telegram.manager")

# Concurrency limit for account restoration
MAX_CONCURRENT_RESTORES = 5


class TelegramClientManager:
    """Manages multiple Telegram client instances"""

    def __init__(self):
        self.clients: Dict[int, Client] = {}
        self.pending_auth: Dict[int, Client] = {}
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.handlers: Dict[int, list] = {}
        self.health_check_task: Optional[asyncio.Task] = None

        # Initialize components
        self.factory = ClientFactory()
        self.auth_handler = AuthHandler()
        self.monitoring_handler = MonitoringHandler()
        self.db_ops = DatabaseOperations()

        Path(settings.SESSIONS_DIR).mkdir(parents=True, exist_ok=True)

    async def startup_restore_accounts(self, db: AsyncSession):
        """Restore active accounts on startup with concurrency control"""
        try:
            accounts = await self.db_ops.get_active_accounts()
            logger.info(f"Found {len(accounts)} active accounts to restore")

            # Restore accounts with concurrency limit
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_RESTORES)

            async def restore_account(account):
                async with semaphore:
                    try:
                        logger.info(f"Restoring account {account.id} [{account.phone_number}]")
                        client, needs_auth = await self.create_client(account, db)

                        if not needs_auth:
                            await self.start_monitoring(account.id, db)
                            logger.info(f"Account {account.id} restored successfully")
                        else:
                            logger.warning(f"Account {account.id} needs re-authentication")
                            await self.db_ops.update_account_status(
                                account.id, AccountStatus.AWAITING_CODE, is_active=False
                            )
                    except FloodWait as e:
                        logger.error(f"FloodWait for account {account.id}: wait {e.value}s")
                        await self.db_ops.handle_error(
                            account.id,
                            f"FloodWait on startup: please wait {e.value} seconds",
                            "flood_wait"
                        )
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        logger.error(f"Failed to restore account {account.id}: {e}")
                        await self.db_ops.handle_error(
                            account.id, f"Startup restore failed: {str(e)}", "startup_error"
                        )

            tasks = [restore_account(account) for account in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)

            self.health_check_task = asyncio.create_task(self._health_check_loop())

        except Exception as e:
            logger.error(f"Error during startup account restore: {e}")

    async def _health_check_loop(self):
        """Periodically check account health"""
        while True:
            try:
                await asyncio.sleep(settings.ACCOUNT_HEALTH_CHECK_INTERVAL)

                async with await self.db_ops._get_session() as db:
                    result = await db.execute(
                        select(TelegramAccount).where(TelegramAccount.is_active == True)
                    )
                    active_accounts = result.scalars().all()

                    for account in active_accounts:
                        client = self.clients.get(account.id)
                        if not client:
                            logger.warning(f"Account {account.id} [{account.phone_number}] is missing client")
                            await self.db_ops.update_account_status(
                                account.id, AccountStatus.STOPPED, is_active=False
                            )
                            continue

                        if not client.is_connected:
                            logger.warning(f"Account {account.id} [{account.phone_number}] is not connected")
                            await self.db_ops.update_account_status(
                                account.id, AccountStatus.STOPPED, is_active=False
                            )
                            continue

                        # Check if account is still valid
                        try:
                            await client.get_me()
                            logger.debug(f"Account {account.id} [{account.phone_number}] health check passed")
                        except Exception as e:
                            logger.error(f"Account {account.id} [{account.phone_number}] health check failed: {e}")
                            await self.db_ops.handle_error(
                                account.id,
                                f"Account validation failed: {str(e)}",
                                "validation_error"
                            )
                            await self.db_ops.update_account_status(
                                account.id, AccountStatus.ERROR, is_active=False
                            )

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def shutdown_all_accounts(self):
        """Stop all active accounts on shutdown"""
        logger.info("Shutting down all Telegram accounts...")

        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        all_account_ids = set(self.clients.keys())
        async with await self.db_ops._get_session() as db:
            result = await db.execute(
                select(TelegramAccount).where(TelegramAccount.is_active == True)
            )
            all_account_ids.update(acc.id for acc in result.scalars().all())

        for account_id in all_account_ids:
            try:
                await self._stop_client_internal(account_id)
            except Exception as e:
                logger.error(f"Error stopping account {account_id}: {e}")

        logger.info("All accounts stopped")

    async def create_client(
            self,
            account: TelegramAccount,
            db: AsyncSession
    ) -> tuple[Client, bool]:
        """Create and initialize a Telegram client"""
        if account.id in self.clients:
            await self.stop_client(account.id, db)
            await asyncio.sleep(1)

        try:
            client, needs_auth = await self.factory.create_client(account, db)

            if needs_auth:
                self.pending_auth[account.id] = client
                await self.db_ops.update_account_status(account.id, AccountStatus.AWAITING_CODE)
            else:
                self.clients[account.id] = client
                await self.db_ops.update_account_status(account.id, AccountStatus.ACTIVE)

            return client, needs_auth

        except Exception as e:
            await self.db_ops.handle_error(account.id, str(e), "auth_error")
            raise

    async def verify_code(
            self,
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            db: AsyncSession
    ) -> bool:
        """Verify authentication code"""
        pending_client = self.pending_auth.get(account_id)
        if not pending_client:
            raise ValueError("No pending authentication for this account")

        try:
            client = await self.auth_handler.verify_code(
                account_id, code, two_fa_password, pending_client, db
            )

            self.pending_auth.pop(account_id)
            self.clients[account_id] = client
            await self.db_ops.update_account_status(account_id, AccountStatus.ACTIVE)

            return True

        except Exception as e:
            error_type = "2fa_error" if "2FA" in str(e) else "verification_error"
            await self.db_ops.handle_error(account_id, str(e), error_type)
            raise

    async def start_monitoring(self, account_id: int, db: AsyncSession):
        """Start message monitoring for an account"""
        client = self.clients.get(account_id)
        if not client:
            logger.warning(f"No client found for account {account_id}")
            return

        account = await self.db_ops.get_account(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return

        # Get active monitoring tasks
        async with await self.db_ops._get_session() as session:
            result = await session.execute(
                select(MonitoringTask).where(
                    MonitoringTask.account_id == account_id,
                    MonitoringTask.is_active == True
                )
            )
            tasks = result.scalars().all()

        # Remove old handlers
        if account_id in self.handlers:
            for handler_tuple in self.handlers[account_id]:
                try:
                    client.remove_handler(handler_tuple[0], handler_tuple[1])
                except Exception as e:
                    logger.warning(f"Could not remove handler: {e}")
            self.handlers[account_id] = []

        # Setup new monitoring
        try:
            handler = await self.monitoring_handler.setup_monitoring(client, account_id, tasks)

            if handler:
                if account_id not in self.handlers:
                    self.handlers[account_id] = []
                self.handlers[account_id].append((handler, account_id))

                await self.db_ops.update_account_status(
                    account_id, AccountStatus.ACTIVE, is_active=True, error_message=None
                )
                logger.info(f"Monitoring started for account {account.phone_number}")

        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            await self.db_ops.handle_error(
                account_id, f"Error starting monitoring: {str(e)}", "monitoring_error"
            )

    async def update_monitoring(self, account_id: int, db: AsyncSession):
        """Update monitoring settings"""
        client = self.clients.get(account_id)
        if not client:
            return

        if account_id in self.handlers:
            for handler_tuple in self.handlers[account_id]:
                try:
                    client.remove_handler(handler_tuple[0], handler_tuple[1])
                except Exception as e:
                    logger.warning(f"Could not remove handler: {e}")
            self.handlers[account_id] = []

        await self.start_monitoring(account_id, db)

    async def _stop_client_internal(self, account_id: int):
        """Internal method to stop client"""
        if account_id in self.handlers:
            client = self.clients.get(account_id)
            if client:
                for handler_tuple in self.handlers[account_id]:
                    try:
                        client.remove_handler(handler_tuple[0], handler_tuple[1])
                    except Exception as e:
                        logger.warning(f"Could not remove handler: {e}")
            self.handlers.pop(account_id, None)

        client = self.clients.pop(account_id, None)
        if client:
            try:
                if client.is_connected:
                    await client.stop()
            except Exception as e:
                logger.warning(f"Error stopping client {account_id}: {e}")

        task = self.running_tasks.pop(account_id, None)
        if task and not task.done():
            task.cancel()

    async def stop_client(self, account_id: int, db: AsyncSession):
        """Stop a Telegram client"""
        await self._stop_client_internal(account_id)
        await self.db_ops.update_account_status(
            account_id, AccountStatus.STOPPED, is_active=False
        )

    async def delete_client(
            self,
            account: TelegramAccount,
            account_id: int,
            db: AsyncSession
    ):
        """Delete a Telegram client and session"""
        await self.stop_client(account_id, db)
        await asyncio.sleep(2)

        session_path = self.factory.get_session_path(account_id)
        session_file = Path(f"{session_path}.session")

        for attempt in range(5):
            try:
                if session_file.exists():
                    session_file.unlink()
                    logger.info(f"Session file deleted for account {account_id}")
                break
            except Exception as e:
                if attempt < 4:
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Error deleting session file: {e}")


telegram_manager = TelegramClientManager()