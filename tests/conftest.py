import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.config import settings
from app.core.db import get_db, db_manager
from app.main import app

# ==========================================
# Core Pytest Configuration
# ==========================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Overrides the default pytest-asyncio event loop to be session-scoped.
    This prevents "Event loop is closed" errors when using session-scoped async fixtures.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==========================================
# Testcontainers: Throwaway PostGIS Database
# ==========================================

@pytest.fixture(scope="session")
def postgis_container():
    """
    Spins up a throwaway PostGIS docker container exclusively for the test run.
    It automatically cleans itself up when tests finish!
    """
    with PostgresContainer("postgis/postgis:15-3.4", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def test_db_setup(postgis_container):
    """
    Hooks the application up to the throwaway container and initializes the DB pools.
    """
    # 1. Dynamically override the application's config to point to the throwaway container
    test_db_url = postgis_container.get_connection_url()
    settings.DATABASE_URL = test_db_url

    # 2. Setup SQLAlchemy ORM engine for the test DB
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    TestSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    
    # 3. Setup the raw asyncpg connection pool used for raw spatial queries
    await db_manager.connect()
    
    # Note: In a real flow, you'd run `alembic upgrade head` right here to create tables!

    yield TestSessionLocal
    
    # Teardown
    await db_manager.disconnect()
    await engine.dispose()


@pytest.fixture
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a fresh, isolated database session for every single test.
    """
    TestSessionLocal = test_db_setup
    async with TestSessionLocal() as session:
        yield session


# ==========================================
# FastAPI HTTP Client Integration
# ==========================================

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides a fully configured async HTTP client for hitting the FastAPI endpoints.
    It automatically intercepts the API's database dependency to inject the test database.
    """
    
    # Dependency Override: Tell FastAPI to use our test `db_session` instead of the real one
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    # Create the HTTP client bridging directly into the FastAPI ASGI app (no network required!)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
        
    # Clear the overrides after the test finishes to keep isolation clean
    app.dependency_overrides.clear()
