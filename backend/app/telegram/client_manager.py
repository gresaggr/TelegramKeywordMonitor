import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, FloodWait
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from app.core.config import settings
from app.core.logger import get_logger
from app.models.account import TelegramAccount, AccountStatus, AccountNotification
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = get_logger("telegram.manager")


class TelegramClientManager:
    """Manages multiple Telegram client instances"""

    def __init__(self):
        self.clients: Dict[int, Client] = {}
        self.pending_auth: Dict[int, Client] = {}
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.handlers: Dict[int, int] = {}
        Path(settings.SESSIONS_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_session_path(account_id: int) -> str:
        """Get session file path for an account"""
        return f"{settings.SESSIONS_DIR}/account_{account_id}"

    async def startup_restore_accounts(self, db: AsyncSession):
        """Restore active accounts on startup"""
        try:
            result = await db.execute(
                select(TelegramAccount).where(
                    TelegramAccount.status == AccountStatus.ACTIVE,
                    TelegramAccount.is_active == True
                )
            )
            accounts = result.scalars().all()

            logger.info(f"Found {len(accounts)} active accounts to restore")

            for account in accounts:
                try:
                    logger.info(f"Restoring account {account.id} [{account.phone_number}]")
                    client, needs_auth = await self.create_client(account, db)

                    if not needs_auth:
                        await self._start_monitoring(account.id, db)
                        logger.info(f"Account {account.id} [{account.phone_number}] restored successfully")
                    else:
                        logger.warning(f"Account {account.id} needs re-authentication")
                        await self._update_account_status(
                            db, account.id, AccountStatus.AWAITING_CODE, is_active=False
                        )
                except Exception as e:
                    logger.error(f"Failed to restore account {account.id}: {e}")
                    await self._handle_error(db, account.id, f"Startup restore failed: {str(e)}", "startup_error")

        except Exception as e:
            logger.error(f"Error during startup account restore: {e}")

    async def create_client(
            self,
            account: TelegramAccount,
            db: AsyncSession
    ) -> Tuple[Client, bool]:
        """
        Create and initialize a Telegram client
        Returns: (client, needs_auth)
        """
        if account.id in self.clients:
            await self.stop_client(account.id, db)
            await asyncio.sleep(1)

        session_path = self._get_session_path(account.id)

        proxy_dict = None
        if account.proxy_host and account.proxy_port:
            proxy_dict = {
                "scheme": "socks5",
                "hostname": account.proxy_host,
                "port": account.proxy_port,
            }
            if account.proxy_username:
                proxy_dict["username"] = account.proxy_username
                proxy_dict["password"] = account.proxy_password

        try:
            client = Client(
                name=f"account_{account.id}",
                api_id=int(account.api_id),
                api_hash=account.api_hash,
                phone_number=account.phone_number,
                device_model=account.device_model or "PC",
                system_version=account.system_version or "Linux",
                app_version=account.app_version or "1.0.0",
                proxy=proxy_dict,
                workdir=settings.SESSIONS_DIR,
                in_memory=False
            )

            await client.connect()

            try:
                await client.get_me()
                logger.info(f"Account {account.id} already authorized")
                self.clients[account.id] = client
                await self._update_account_status(db, account.id, AccountStatus.ACTIVE)
                return client, False
            except:
                pass

            sent_code = await client.send_code(account.phone_number)

            from sqlalchemy.ext.asyncio import async_sessionmaker
            from app.db.session import engine
            async_session = async_sessionmaker(engine, expire_on_commit=False)
            async with async_session() as new_session:
                await new_session.execute(
                    update(TelegramAccount)
                    .where(TelegramAccount.id == account.id)
                    .values(phone_code_hash=sent_code.phone_code_hash)
                )
                await new_session.commit()

            self.pending_auth[account.id] = client

            await self._update_account_status(db, account.id, AccountStatus.AWAITING_CODE)
            logger.info(f"Auth code sent to {account.phone_number}, phone_code_hash saved")
            return client, True

        except FloodWait as e:
            error_msg = f"Flood wait: please wait {e.value} seconds"
            logger.error(f"FloodWait for account {account.id}: {error_msg}")
            await self._handle_error(db, account.id, error_msg, "flood_wait")
            raise ValueError(error_msg)

        except Exception as e:
            error_msg = f"Error creating client: {str(e)}"
            logger.error(f"Error for account {account.id}: {error_msg}")
            await self._handle_error(db, account.id, error_msg, "auth_error")
            raise

    async def verify_code(
            self,
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            db: AsyncSession
    ) -> bool:
        """Verify authentication code and optionally 2FA password"""
        client = self.pending_auth.get(account_id)
        if not client:
            raise ValueError("No pending authentication for this account")

        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker
            from app.db.session import engine
            async_session = async_sessionmaker(engine, expire_on_commit=False)

            async with async_session() as new_session:
                result = await new_session.execute(
                    select(TelegramAccount).where(TelegramAccount.id == account_id)
                )
                account: TelegramAccount = result.scalar_one_or_none()
                if not account:
                    raise ValueError("Account not found")

                if not account.phone_code_hash:
                    raise ValueError("Phone code hash not found. Please request a new code.")

                phone_code_hash = account.phone_code_hash

            await client.sign_in(
                phone_number=account.phone_number,
                phone_code_hash=phone_code_hash,
                phone_code=code
            )

            self.pending_auth.pop(account_id)
            self.clients[account_id] = client

            async with async_session() as new_session:
                await new_session.execute(
                    update(TelegramAccount)
                    .where(TelegramAccount.id == account_id)
                    .values(phone_code_hash=None, error_message=None)
                )
                await new_session.commit()

            await self._update_account_status(db, account_id, AccountStatus.ACTIVE)
            await self._start_monitoring(account_id, db)

            logger.info(f"Account {account_id} [{account.phone_number}] successfully authorized")
            return True

        except SessionPasswordNeeded:
            if not two_fa_password:
                await self._update_account_status(db, account_id, AccountStatus.AWAITING_2FA)
                raise ValueError("2FA password required")

            try:
                await client.check_password(two_fa_password)
                self.pending_auth.pop(account_id)
                self.clients[account_id] = client

                from sqlalchemy.ext.asyncio import async_sessionmaker
                from app.db.session import engine
                async_session = async_sessionmaker(engine, expire_on_commit=False)

                async with async_session() as new_session:
                    await new_session.execute(
                        update(TelegramAccount)
                        .where(TelegramAccount.id == account_id)
                        .values(phone_code_hash=None, error_message=None)
                    )
                    await new_session.commit()

                await self._update_account_status(db, account_id, AccountStatus.ACTIVE)
                await self._start_monitoring(account_id, db)

                logger.info(f"Account {account_id} [{account.phone_number}] authorized with 2FA")
                return True

            except Exception as e:
                error_msg = f"Invalid 2FA password: {str(e)}"
                await self._handle_error(db, account_id, error_msg, "2fa_error")
                raise ValueError(error_msg)

        except PhoneCodeInvalid:
            error_msg = "Invalid verification code"
            await self._handle_error(db, account_id, error_msg, "code_error")
            raise ValueError(error_msg)

        except PhoneCodeExpired:
            error_msg = "Verification code expired. Please request a new code."
            from sqlalchemy.ext.asyncio import async_sessionmaker
            from app.db.session import engine
            async_session = async_sessionmaker(engine, expire_on_commit=False)

            async with async_session() as new_session:
                await new_session.execute(
                    update(TelegramAccount)
                    .where(TelegramAccount.id == account_id)
                    .values(phone_code_hash=None)
                )
                await new_session.commit()

            await self._handle_error(db, account_id, error_msg, "code_expired")
            raise ValueError(error_msg)

        except Exception as e:
            error_msg = f"Error verifying code: {str(e)}"
            logger.error(f"Error for account {account_id}: {error_msg}")
            await self._handle_error(db, account_id, error_msg, "verification_error")
            raise

    async def _start_monitoring(self, account_id: int, db: AsyncSession):
        """Start message monitoring for an account"""
        client = self.clients.get(account_id)
        if not client:
            logger.warning(f"No client found for account {account_id}")
            return

        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.db.session import engine
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as new_session:
            result = await new_session.execute(
                select(TelegramAccount).where(TelegramAccount.id == account_id)
            )
            account: TelegramAccount = result.scalar_one_or_none()
            if not account:
                logger.error(f"Account {account_id} not found in database")
                return

            whitelist = json.loads(account.whitelist_keywords or "[]")
            blacklist = json.loads(account.blacklist_keywords or "[]")
            channels = json.loads(account.monitored_channels or "[]")
            forward_to = account.forward_to_chat_id
            replacements = json.loads(account.replacements or "{}")

        if not channels:
            logger.warning(f"No channels configured for account {account.phone_number}")
            return

        if not forward_to:
            logger.warning(f"No forward destination configured for account {account.phone_number}")
            return

        channel_filters = []
        for ch in channels:
            try:
                if ch.lstrip('-').isdigit():
                    channel_filters.append(int(ch))
                else:
                    channel_filters.append(ch)
            except:
                logger.warning(f"Invalid channel identifier: {ch}")

        if not channel_filters:
            logger.error(f"No valid channels for account {account.phone_number}")
            return

        logger.info(f"Setting up monitoring for account {account.phone_number} on channels: {channel_filters}")

        if account_id in self.handlers:
            try:
                client.remove_handler(*self.handlers[account_id])
            except:
                pass

        async def handle_message(client_instance: Client, message: Message):
            try:
                text = message.text or message.caption or ""
                if not text:
                    return

                text_lower = text.lower()

                has_whitelist_match = True
                if whitelist:
                    has_whitelist_match = any(
                        keyword.lower() in text_lower for keyword in whitelist
                    )

                has_blacklist_match = False
                if blacklist:
                    has_blacklist_match = any(
                        keyword.lower() in text_lower for keyword in blacklist
                    )

                if has_whitelist_match and not has_blacklist_match:
                    modified_text = text
                    if replacements:
                        for old_text, new_text in replacements.items():
                            modified_text = modified_text.replace(old_text, new_text)

                    forward_chat_id = int(forward_to) if forward_to.lstrip('-').isdigit() else forward_to

                    if modified_text != text:
                        await client_instance.send_message(
                            chat_id=forward_chat_id,
                            text=modified_text
                        )
                    else:
                        await message.forward(chat_id=forward_chat_id)

                    from sqlalchemy.ext.asyncio import async_sessionmaker
                    from app.db.session import engine
                    async_session_new = async_sessionmaker(engine, expire_on_commit=False)
                    async with async_session_new() as session:
                        await session.execute(
                            update(TelegramAccount)
                            .where(TelegramAccount.id == account_id)
                            .values(last_activity=datetime.now(timezone.utc))
                        )
                        await session.commit()

                    logger.info(f"Message forwarded from account {account_id}")

            except Exception as e:
                logger.error(f"Error handling message for account {account_id}: {e}")
                from sqlalchemy.ext.asyncio import async_sessionmaker
                from app.db.session import engine
                async_session_new = async_sessionmaker(engine, expire_on_commit=False)
                async with async_session_new() as error_session:
                    await self._handle_error(error_session, account_id, f"Message forwarding error: {str(e)}",
                                             "forwarding_error")

        try:
            handler = MessageHandler(
                callback=handle_message,
                filters=filters.chat(channel_filters)
            )

            if not client.is_connected:
                await client.start()

            handler_group = client.add_handler(handler, group=account_id)
            self.handlers[account_id] = (handler_group, account_id)

            async with async_session() as new_session:
                result = await new_session.execute(
                    select(TelegramAccount).where(TelegramAccount.id == account_id)
                )
                acc = result.scalar_one_or_none()
                if acc:
                    acc.is_active = True
                    acc.error_message = None
                    await new_session.commit()

            logger.info(f"Monitoring started for account {account.phone_number}")

        except Exception as e:
            logger.error(f"Error starting monitoring for account {account_id}: {e}")
            await self._handle_error(db, account_id, f"Error starting monitoring: {str(e)}", "monitoring_error")

    async def stop_client(self, account_id: int, db: AsyncSession):
        """Stop a Telegram client"""
        if account_id in self.handlers:
            try:
                client = self.clients.get(account_id)
                if client:
                    client.remove_handler(*self.handlers[account_id])
            except:
                pass
            self.handlers.pop(account_id, None)

        client = self.clients.pop(account_id, None)

        if client:
            try:
                if client.is_connected:
                    await client.stop()
                logger.info(f"Client stopped for account {account_id}")
            except Exception as e:
                logger.error(f"Error stopping client {account_id}: {e}")

        task = self.running_tasks.pop(account_id, None)
        if task and not task.done():
            task.cancel()

        await self._update_account_status(db, account_id, AccountStatus.STOPPED, is_active=False)

    async def delete_client(self, account_id: int, db: AsyncSession):
        """Delete a Telegram client and its session"""
        await self.stop_client(account_id, db)

        await asyncio.sleep(2)

        session_path = self._get_session_path(account_id)
        session_file = Path(f"{session_path}.session")

        for attempt in range(5):
            try:
                if session_file.exists():
                    session_file.unlink()
                    logger.info(f"Session file deleted for account {account_id}")
                break
            except Exception as e:
                if attempt < 4:
                    logger.warning(f"Attempt {attempt + 1}/5: Could not delete session file, retrying...")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Error deleting session file after 5 attempts: {e}")

    async def update_client_settings(self, account_id: int, db: AsyncSession):
        """Update monitoring settings for a running client"""
        await self.stop_client(account_id, db)
        await asyncio.sleep(1)

        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.db.session import engine
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as new_session:
            result = await new_session.execute(
                select(TelegramAccount).where(TelegramAccount.id == account_id)
            )
            account = result.scalar_one_or_none()

        if account and account.status != AccountStatus.STOPPED:
            try:
                client, needs_auth = await self.create_client(account, db)
                if not needs_auth:
                    await self._start_monitoring(account_id, db)
            except Exception as e:
                logger.error(f"Error updating client {account_id}: {e}")
                await self._handle_error(db, account_id, f"Error updating: {str(e)}", "update_error")

    async def _update_account_status(
            self,
            db: AsyncSession,
            account_id: int,
            status: AccountStatus,
            error_message: Optional[str] = None,
            is_active: Optional[bool] = None
    ):
        """Update account status in database"""
        values = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if is_active is not None:
            values["is_active"] = is_active

        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.db.session import engine
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as new_session:
            await new_session.execute(
                update(TelegramAccount)
                .where(TelegramAccount.id == account_id)
                .values(**values)
            )
            await new_session.commit()

    async def _handle_error(
            self,
            db: AsyncSession,
            account_id: int,
            error_message: str,
            error_type: str
    ):
        """Handle errors by updating status and creating notifications"""
        await self._update_account_status(
            db, account_id, AccountStatus.ERROR, error_message, is_active=False
        )

        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.db.session import engine
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as new_session:
            notification = AccountNotification(
                account_id=account_id,
                message=error_message,
                error_type=error_type
            )
            new_session.add(notification)
            await new_session.commit()

        if settings.TELEGRAM_BOT_TOKEN and settings.ADMIN_TELEGRAM_CHAT_ID:
            try:
                from app.services.telegram import send_telegram_notification
                error_safe = error_message.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`',
                                                                                                               '\\`')
                admin_message = (
                    f"⚠️ *Telegram Account Error*\n\n"
                    f"*Account ID:* {account_id}\n"
                    f"*Error Type:* {error_type}\n"
                    f"*Message:* {error_safe}\n"
                    f"*Time:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
                )
                await send_telegram_notification(settings.ADMIN_TELEGRAM_CHAT_ID, admin_message)
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")

        logger.error(f"Error handled for account {account_id}: {error_message}")


telegram_manager = TelegramClientManager()