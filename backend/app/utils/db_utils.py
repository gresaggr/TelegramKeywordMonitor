"""Database utility functions"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager


@asynccontextmanager
async def get_independent_session():
    """
    Create an independent database session that can be used
    outside of the main request-response cycle
    """
    from app.db.session import engine

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
