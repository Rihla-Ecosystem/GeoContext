from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.db import get_db, db_manager

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up GeoContext API...")
    await db_manager.connect()
    yield
    logger.info("Shutting down GeoContext API...")
    await db_manager.disconnect()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

setup_exception_handlers(app)


# ==========================================
# Health Probes
# ==========================================

@app.get("/healthz", tags=["health"])
async def liveness_probe():
    """
    Liveness probe.
    Returns 200 OK immediately if the web server is running and accepting connections.
    """
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe.
    Returns 200 OK only if the application is fully ready to handle traffic,
    which includes verifying a successful connection to the PostGIS database.
    """
    try:
        # Perform a simple query to verify ORM DB connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness probe failed", error=str(e))
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not ready"
        )
