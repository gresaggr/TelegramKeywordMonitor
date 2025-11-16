"""Handler for message monitoring and forwarding"""
import json
from datetime import datetime, timezone
from typing import Set, List

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from app.core.logger import get_logger
from app.models.account import TelegramAccount, MonitoringTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = get_logger("telegram.monitoring")


class MonitoringHandler:
    """Handles message monitoring and forwarding"""

    @staticmethod
    def _parse_channels(tasks: List[MonitoringTask]) -> Set:
        """Parse and validate channel identifiers from tasks"""
        all_channels = set()
        for task in tasks:
            channels = json.loads(task.monitored_channels or "[]")
            for ch in channels:
                try:
                    if ch.lstrip('-').isdigit():
                        all_channels.add(int(ch))
                    else:
                        all_channels.add(ch)
                except:
                    logger.warning(f"Invalid channel identifier: {ch}")
        return all_channels

    @staticmethod
    def _check_message_match(
            text: str,
            whitelist: List[str],
            blacklist: List[str]
    ) -> bool:
        """Check if message matches whitelist and doesn't match blacklist"""
        text_lower = text.lower()

        # Check whitelist
        has_whitelist_match = True
        if whitelist:
            has_whitelist_match = any(
                keyword.lower() in text_lower for keyword in whitelist
            )

        # Check blacklist
        has_blacklist_match = False
        if blacklist:
            has_blacklist_match = any(
                keyword.lower() in text_lower for keyword in blacklist
            )

        return has_whitelist_match and not has_blacklist_match

    @staticmethod
    def _apply_replacements(text: str, replacements: dict) -> str:
        """Apply text replacements"""
        modified_text = text
        if replacements:
            for old_text, new_text in replacements.items():
                modified_text = modified_text.replace(old_text, new_text)
        return modified_text

    @staticmethod
    def _check_channel_match(message: Message, channels: List[str]) -> bool:
        """Check if message is from one of monitored channels"""
        for ch in channels:
            if ch.lstrip('-').isdigit():
                if message.chat.id == int(ch):
                    return True
            else:
                if message.chat.username and message.chat.username.lower() == ch.lstrip('@').lower():
                    return True
        return False

    @staticmethod
    def _get_message_link(message: Message) -> str:
        """Generate link to original message"""
        if message.chat.username:
            return f"https://t.me/{message.chat.username}/{message.id}"
        else:
            chat_id = str(message.chat.id).replace('-100', '')
            return f"https://t.me/c/{chat_id}/{message.id}"

    async def create_message_handler(
            self,
            account_id: int,
            channels: Set
    ):
        """Create message handler for monitoring"""

        async def handle_message(client_instance: Client, message: Message):
            try:
                text = message.text or message.caption or ""
                if not text:
                    return

                # Get active tasks from database
                from sqlalchemy.ext.asyncio import async_sessionmaker
                from app.db.session import engine
                async_session = async_sessionmaker(engine, expire_on_commit=False)

                async with async_session() as session:
                    result = await session.execute(
                        select(MonitoringTask).where(
                            MonitoringTask.account_id == account_id,
                            MonitoringTask.is_active == True
                        )
                    )
                    active_tasks = result.scalars().all()

                    # Process each active task
                    for task in active_tasks:
                        channels_list = json.loads(task.monitored_channels or "[]")

                        # Check if message is from monitored channel
                        if not self._check_channel_match(message, channels_list):
                            continue

                        # Parse task settings
                        whitelist = json.loads(task.whitelist_keywords or "[]")
                        blacklist = json.loads(task.blacklist_keywords or "[]")
                        replacements = json.loads(task.replacements or "{}")

                        # Check if message matches criteria
                        if self._check_message_match(text, whitelist, blacklist):
                            # Apply replacements
                            modified_text = self._apply_replacements(text, replacements)

                            # Add source link if enabled
                            if task.include_source_link:
                                source_link = self._get_message_link(message)
                                modified_text += f"\n\nпереслано с {source_link}"

                            # Forward message
                            forward_chat_id = (
                                int(task.forward_to_chat_id)
                                if task.forward_to_chat_id.lstrip('-').isdigit()
                                else task.forward_to_chat_id
                            )

                            await client_instance.send_message(
                                chat_id=forward_chat_id,
                                text=modified_text
                            )

                            # Update last activity
                            await session.execute(
                                update(TelegramAccount)
                                .where(TelegramAccount.id == account_id)
                                .values(last_activity=datetime.now(timezone.utc))
                            )
                            await session.commit()

                            logger.info(f"Message sent from account {account_id} (task: {task.name})")
                            break

            except Exception as e:
                logger.error(f"Error handling message for account {account_id}: {e}")

        return MessageHandler(
            callback=handle_message,
            filters=filters.chat(list(channels))
        )

    async def setup_monitoring(
            self,
            client: Client,
            account_id: int,
            tasks: List[MonitoringTask]
    ):
        """Setup monitoring for account"""
        if not tasks:
            logger.warning(f"No active monitoring tasks for account {account_id}")
            return None

        # Parse all channels
        all_channels = self._parse_channels(tasks)
        if not all_channels:
            logger.error(f"No valid channels for account {account_id}")
            return None

        logger.info(f"Setting up monitoring for account {account_id} on channels: {all_channels}")

        # Create handler
        handler = await self.create_message_handler(account_id, all_channels)

        # Initialize client if needed
        if not client.is_connected:
            await client.connect()

        if not client.is_initialized:
            await client.initialize()

        # Add handler
        client.add_handler(handler, group=account_id)

        return handler