from typing import AsyncGenerator

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    #FastAPI dependency for providing a SQLAlchemy AsyncSession
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


ASYNC_PG_URL = settings.DATABASE_URL.replace("+asyncpg", "")

class DatabaseManager:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """Initialize the raw asyncpg pool. Should be called on app startup."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                ASYNC_PG_URL,
                min_size=2,
                max_size=10,
            )

    async def disconnect(self):
        """Close the raw asyncpg pool. Should be called on app shutdown."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


db_manager = DatabaseManager()

async def get_raw_pool() -> asyncpg.Pool:
    """
    FastAPI dependency for providing the raw asyncpg pool.
    Useful for running heavy raw spatial queries with PostGIS.
    """
    if db_manager.pool is None:
        raise RuntimeError("asyncpg pool is not initialized. Make sure to call db_manager.connect() on startup.")
    return db_manager.pool
