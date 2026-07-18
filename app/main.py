from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.db import get_db, db_manager, engine

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up GeoContext API...")
    await db_manager.connect()
    yield
    logger.info("Shutting down GeoContext API...")
    await db_manager.disconnect()


from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin

from app.api.context import router as context_router
from app.api.sites import router as sites_router
from app.api.reports import router as reports_router
from app.services.rate_limit import limiter
from app.admin.auth_backend import authentication_backend
from app.admin.views import SiteAdmin, BoundaryAdmin, RestrictedZoneAdmin, ReportAdmin, AuditLogAdmin

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Required for SQLAdmin auth backend
app.add_middleware(SessionMiddleware, secret_key="geocontext-admin-super-secret-key-replace-in-prod")

# Register SQLAdmin Dashboard
admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(SiteAdmin)
admin.add_view(BoundaryAdmin)
admin.add_view(RestrictedZoneAdmin)
admin.add_view(ReportAdmin)
admin.add_view(AuditLogAdmin)

# Register SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

setup_exception_handlers(app)

app.include_router(context_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


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


# ==========================================
# Static UI
# ==========================================

app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")
