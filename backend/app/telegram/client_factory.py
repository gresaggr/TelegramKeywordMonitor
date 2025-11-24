"""Factory for creating Telegram clients"""
from pathlib import Path
from typing import Tuple

from pyrogram import Client
from pyrogram.errors import FloodWait

from app.core.config import settings
from app.core.logger import get_logger
from app.models.account import TelegramAccount, AccountStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

logger = get_logger("telegram.factory")


class ClientFactory:
    """Factory for creating and initializing Telegram clients"""

    @staticmethod
    def get_session_path(account_id: int) -> str:
        """Get session file path for an account"""
        Path(settings.SESSIONS_DIR).mkdir(parents=True, exist_ok=True)
        return f"{settings.SESSIONS_DIR}/account_{account_id}"

    @staticmethod
    def _create_proxy_dict(account: TelegramAccount) -> dict | None:
        """Create proxy configuration dictionary"""
        if not account.proxy_host or not account.proxy_port:
            return None

        proxy_dict = {
            "scheme": "socks5",
            "hostname": account.proxy_host,
            "port": account.proxy_port,
        }

        if account.proxy_username:
            proxy_dict["username"] = account.proxy_username
            proxy_dict["password"] = account.proxy_password

        return proxy_dict

    async def create_client(
            self,
            account: TelegramAccount,
            db: AsyncSession
    ) -> Tuple[Client, bool]:
        """
        Create and initialize a Telegram client
        Returns: (client, needs_auth)
        """
        proxy_dict = self._create_proxy_dict(account)

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

            logger.info(f"Auth code sent to {account.phone_number}")
            return client, True

        except FloodWait as e:
            error_msg = f"Flood wait: please wait {e.value} seconds"
            logger.error(f"FloodWait for account {account.id}: {error_msg}")
            raise ValueError(error_msg)

        except Exception as e:
            error_msg = f"Error creating client: {str(e)}"
            logger.error(f"Error for account {account.id}: {error_msg}")
            raise
