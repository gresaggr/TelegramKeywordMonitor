from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token, verify_password, get_password_hash
from app.services.telegram import validate_telegram_chat_id
from app.core.logger import get_logger

logger = get_logger("services.auth")


class AuthService:
    @staticmethod
    async def register_user(user_data: UserCreate, db: AsyncSession) -> User:
        """Register a new user"""
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise ValueError("Username already taken")

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            balance=0.0,
            language="en",
            default_api_id="2040",
            default_api_hash="b18441a1ff607e10a989891a5462e627",
            default_device_model="MS-7C75",
            default_system_version="Windows 10",
            default_app_version="4.8.3"
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"New user registered: {new_user.email}")
        return new_user

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> str:
        """Authenticate user and return access token"""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect email or password")

        if not user.is_active:
            raise ValueError("Inactive user")

        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"User logged in: {user.email}")

        return access_token

    @staticmethod
    async def update_user_profile(user: User, user_data: UserUpdate, db: AsyncSession) -> User:
        """Update user profile"""
        if user_data.default_telegram_chat_id is not None:
            if user_data.default_telegram_chat_id:
                is_valid = await validate_telegram_chat_id(user_data.default_telegram_chat_id)
                if not is_valid:
                    raise ValueError("Invalid Telegram chat ID. Make sure you've started the bot.")
            user.default_telegram_chat_id = user_data.default_telegram_chat_id or None

        if user_data.default_api_id is not None:
            user.default_api_id = user_data.default_api_id
        if user_data.default_api_hash is not None:
            user.default_api_hash = user_data.default_api_hash
        if user_data.default_device_model is not None:
            user.default_device_model = user_data.default_device_model
        if user_data.default_system_version is not None:
            user.default_system_version = user_data.default_system_version
        if user_data.default_app_version is not None:
            user.default_app_version = user_data.default_app_version
        if user_data.default_forward_to_chat_id is not None:
            user.default_forward_to_chat_id = user_data.default_forward_to_chat_id
        if user_data.language is not None:
            if user_data.language not in ["en", "ru"]:
                raise ValueError("Invalid language. Must be 'en' or 'ru'")
            user.language = user_data.language

        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.id} profile updated")
        return user