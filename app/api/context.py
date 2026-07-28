from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.core.config import settings
from app.core.db import get_db
from app.schemas.context import ContextResponse
from app.services.spatial import get_spatial_context

from app.core.security import allow_access

router = APIRouter(prefix="/context", tags=["Context"])

@router.get("", response_model=ContextResponse)
async def fetch_spatial_context(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude of the location"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude of the location"),
    radius: Optional[float] = Query(None, description="Detection radius in meters for nearby sites"),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    """
    Given a lat/lon coordinate, return the comprehensive spatial context including:
    - Whether the point is within Egypt's borders
    - The specific Governorate
    - If the user is currently AT a site
    - Other nearby sites within the detection radius
    - Any restricted or warning zones the user is currently intersecting
    """
    # Use default from config if not provided
    effective_radius = radius if radius is not None else settings.DEFAULT_DETECTION_RADIUS
    
    # Cap the radius to the system maximum
    effective_radius = min(effective_radius, settings.MAX_DETECTION_RADIUS)
    
    # Ensure radius is non-negative
    if effective_radius < 0:
        raise HTTPException(status_code=400, detail="Radius cannot be negative")

    return await get_spatial_context(session, lat, lon, effective_radius)
