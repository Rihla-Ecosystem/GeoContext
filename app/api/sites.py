from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, and_
from geoalchemy2 import Geography
from typing import Optional, List

from app.core.config import settings
from app.core.db import get_db
from app.models.site import Site
from app.models.boundary import Boundary
from app.schemas.site import NearbySiteResponse

router = APIRouter(prefix="/nearby-sites", tags=["Sites"])

@router.get("", response_model=List[NearbySiteResponse])
async def get_nearby_sites(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    radius: Optional[float] = Query(None, description="Search radius in meters"),
    category: Optional[str] = Query(None, description="Filter by site category (e.g. archaeological, islamic, christian)"),
    session: AsyncSession = Depends(get_db)
):
    """
    Finds all sites within a specific radius of a coordinate.
    Supports filtering by category and spatially joins the Governorate name.
    """
    effective_radius = radius if radius is not None else settings.DEFAULT_DETECTION_RADIUS
    effective_radius = min(effective_radius, settings.MAX_DETECTION_RADIUS)
    
    if effective_radius < 0:
        raise HTTPException(status_code=400, detail="Radius cannot be negative")

    point_geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    # Use an OUTER JOIN with ST_Intersects to instantly find which governorate polygon the site point falls into!
    query = select(
        Site, 
        func.ST_Distance(
            cast(Site.geometry, Geography), 
            cast(point_geom, Geography)
        ).label("distance"),
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon"),
        Boundary.name_en.label("governorate_name")
    ).outerjoin(
        Boundary,
        and_(
            Boundary.level == 'governorate',
            func.ST_Intersects(Boundary.geometry, Site.geometry)
        )
    ).where(
        func.ST_DWithin(
            cast(Site.geometry, Geography), 
            cast(point_geom, Geography), 
            effective_radius
        )
    )

    if category:
        query = query.where(Site.category == category)

    query = query.order_by("distance")
    
    result = await session.execute(query)
    
    response = []
    for site, distance, site_lat, site_lon, gov_name in result:
        response.append(NearbySiteResponse(
            id=site.id,
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            category=site.category,
            description=site.description,
            details=site.description,
            governorate=gov_name,
            distance_meters=round(distance, 2),
            lat=site_lat,
            lon=site_lon
        ))
        
    return response


@router.get("/by-governorate", response_model=List[NearbySiteResponse])
async def get_sites_by_governorate(
    governorate_name: str = Query(..., description="Name of the governorate (e.g., 'Cairo', 'Alexandria')"),
    category: Optional[str] = Query(None, description="Filter by site category"),
    session: AsyncSession = Depends(get_db)
):
    """
    Finds all sites within a specific Governorate polygon.
    """
    # 1. First, find the governorate polygon by name
    gov_query = select(Boundary).where(
        Boundary.level == 'governorate',
        func.lower(Boundary.name_en).like(f"%{governorate_name.lower()}%")
    ).limit(1)
    
    gov_result = await session.execute(gov_query)
    governorate = gov_result.scalars().first()
    
    if not governorate:
        raise HTTPException(status_code=404, detail=f"Governorate matching '{governorate_name}' not found")
        
    # 2. Find all sites that intersect with this governorate's geometry
    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon")
    ).where(
        func.ST_Intersects(Site.geometry, governorate.geometry)
    )
    
    if category:
        query = query.where(Site.category == category)
        
    result = await session.execute(query)
    
    response = []
    for site, site_lat, site_lon in result:
        response.append(NearbySiteResponse(
            id=site.id,
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            category=site.category,
            description=site.description,
            details=site.description,
            governorate=governorate.name_en,
            distance_meters=0.0, # Not applicable for this endpoint
            lat=site_lat,
            lon=site_lon
        ))
        
    return response
