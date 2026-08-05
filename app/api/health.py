from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.db import get_db
from app.core.security import allow_access

logger = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])

TABLE_MODELS = [
    ("sites", "Site"),
    ("boundaries", "Boundary"),
    ("restricted_zones", "RestrictedZone"),
    ("audit_logs", "AuditLog"),
]


@router.get("/models")
async def health_models(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    """List GeoContext data tables with current row counts (admin/internal)."""
    models = []
    for table, model in TABLE_MODELS:
        try:
            result = await session.execute(text(f"SELECT COUNT(*) AS c FROM {table}"))
            count = result.scalar() or 0
            models.append({"name": model, "table": table, "count": count})
        except Exception as e:
            logger.warning("Table count failed", table=table, error=str(e))
            models.append({"name": model, "table": table, "count": 0})

    return {"status": "ok", "models": models}
