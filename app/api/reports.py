from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
import structlog

from app.core.db import get_db
from app.schemas.report import ReportCreate, ReportResponse
from app.models.report import Report
from app.services.rate_limit import limiter

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = structlog.get_logger()

from app.core.security import get_current_user

@router.post("", response_model=ReportResponse, status_code=201)
@limiter.limit("5/minute")
async def submit_report(
    request: Request,
    payload: ReportCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Submits a new spatial report.
    By design, this always defaults to 'pending' to ensure no auto-trust path exists.
    Rate limited to 5 submissions per minute per IP.
    """
    new_report = Report(
        report_type=payload.report_type,
        description=payload.description,
        severity=payload.severity,
        related_site_id=payload.related_site_id,
        geometry=func.ST_SetSRID(func.ST_MakePoint(payload.lon, payload.lat), 4326),
        status="pending" # Hardcoded to 'pending', ignoring any status sent by user
    )
    
    session.add(new_report)
    await session.commit()
    await session.refresh(new_report)
    
    logger.info("Report submitted successfully", report_id=str(new_report.id), report_type=payload.report_type)
    
    return ReportResponse(
        id=new_report.id,
        report_type=new_report.report_type,
        description=new_report.description,
        severity=new_report.severity,
        lat=payload.lat,
        lon=payload.lon,
        related_site_id=new_report.related_site_id,
        status=new_report.status
    )
