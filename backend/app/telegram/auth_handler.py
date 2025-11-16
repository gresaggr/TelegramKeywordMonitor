"""Handler for Telegram authentication"""
from typing import Optional

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

from app.core.logger import get_logger
from app.models.account import TelegramAccount
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = get_logger("telegram.auth")


class AuthHandler:
    """Handles Telegram authentication process"""

    async def verify_code(
            self,
            account_id: int,
            code: str,
            two_fa_password: Optional[str],
            pending_client: Client,
            db: AsyncSession
    ) -> Client:
        """
        Verify authentication code and optionally 2FA password
        Returns: Authenticated client
        """
        try:
            # Get account and phone_code_hash
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

            # Try to sign in with code
            await pending_client.sign_in(
                phone_number=account.phone_number,
                phone_code_hash=phone_code_hash,
                phone_code=code
            )

            # Clear phone_code_hash on success
            await self._clear_phone_code_hash(account_id)

            logger.info(f"Account {account_id} [{account.phone_number}] successfully authorized")
            return pending_client

        except SessionPasswordNeeded:
            return await self._handle_2fa(account_id, two_fa_password, pending_client)

        except PhoneCodeInvalid:
            raise ValueError("Invalid verification code")

        except PhoneCodeExpired:
            await self._clear_phone_code_hash(account_id)
            raise ValueError("Verification code expired. Please request a new code.")

        except Exception as e:
            error_msg = f"Error verifying code: {str(e)}"
            logger.error(f"Error for account {account_id}: {error_msg}")
            raise

    async def _handle_2fa(
            self,
            account_id: int,
            two_fa_password: Optional[str],
            client: Client
    ) -> Client:
        """Handle 2FA authentication"""
        if not two_fa_password:
            raise ValueError("2FA password required")

        try:
            await client.check_password(two_fa_password)
            await self._clear_phone_code_hash(account_id)
            logger.info(f"Account {account_id} authorized with 2FA")
            return client

        except Exception as e:
            error_msg = f"Invalid 2FA password: {str(e)}"
            raise ValueError(error_msg)

    async def _clear_phone_code_hash(self, account_id: int):
        """Clear phone_code_hash after successful authentication"""
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
