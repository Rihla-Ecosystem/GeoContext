from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, and_
from geoalchemy2 import Geography
from typing import Optional, List
import structlog

from app.core.config import settings
from app.core.db import get_db
from app.models.site import Site
from app.models.boundary import Boundary
from app.schemas.site import NearbySiteResponse, SiteCreate, SiteUpdate, SiteResponse
from app.core.security import allow_access, require_admin

logger = structlog.get_logger()

router = APIRouter(prefix="/nearby-sites", tags=["Sites"])
admin_router = APIRouter(prefix="/sites", tags=["Sites Admin"])


@router.get("", response_model=List[NearbySiteResponse])
async def get_nearby_sites(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    radius: Optional[float] = Query(None, description="Search radius in meters"),
    category: Optional[str] = Query(None, description="Filter by site category (e.g. archaeological, islamic, christian)"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Max results"),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    effective_radius = radius if radius is not None else settings.DEFAULT_DETECTION_RADIUS
    effective_radius = min(effective_radius, settings.MAX_DETECTION_RADIUS)

    if effective_radius < 0:
        raise HTTPException(status_code=400, detail="Radius cannot be negative")

    point_geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

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
        query = query.where(Site.categories.contains([category]))

    query = query.order_by("distance")

    if limit:
        query = query.limit(limit)

    result = await session.execute(query)

    seen = set()
    response = []
    for site, distance, site_lat, site_lon, gov_name in result:
        if site.id in seen:
            continue
        seen.add(site.id)
        response.append(NearbySiteResponse(
            id=site.id,
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            categories=site.categories,
            details=site.details,
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
    limit: Optional[int] = Query(None, ge=1, le=500, description="Max results"),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    gov_query = select(Boundary).where(
        Boundary.level == 'governorate',
        func.lower(Boundary.name_en).like(f"%{governorate_name.lower()}%")
    ).limit(1)

    gov_result = await session.execute(gov_query)
    governorate = gov_result.scalars().first()

    if not governorate:
        raise HTTPException(status_code=404, detail=f"Governorate matching '{governorate_name}' not found")

    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon")
    ).where(
        func.ST_Intersects(Site.geometry, governorate.geometry)
    )

    if category:
        query = query.where(Site.categories.contains([category]))

    if limit:
        query = query.limit(limit)

    result = await session.execute(query)

    response = []
    for site, site_lat, site_lon in result:
        response.append(NearbySiteResponse(
            id=site.id,
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            categories=site.categories,
            details=site.details,
            governorate=governorate.name_en,
            distance_meters=0.0,
            lat=site_lat,
            lon=site_lon
        ))

    return response


@admin_router.get("", response_model=List[SiteResponse])
async def list_sites(
    site_type: str | None = None,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon")
    )
    if site_type:
        query = query.where(Site.site_type == site_type)
    query = query.order_by(Site.name)

    result = await session.execute(query)

    return [
        SiteResponse(
            id=s.id,
            osm_type=s.osm_type,
            osm_id=s.osm_id,
            name=s.name,
            name_en=s.name_en,
            name_ar=s.name_ar,
            details=s.details,
            categories=s.categories,
            site_type=s.site_type,
            lat=lat,
            lon=lon
        )
        for s, lat, lon in result
    ]


@admin_router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon")
    ).where(Site.id == site_id)
    result = await session.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")
    site, lat, lon = row
    return SiteResponse(
        id=site.id,
        osm_type=site.osm_type,
        osm_id=site.osm_id,
        name=site.name,
        name_en=site.name_en,
        name_ar=site.name_ar,
        details=site.details,
        categories=site.categories,
        site_type=site.site_type,
        lat=lat,
        lon=lon
    )


@admin_router.post("", response_model=SiteResponse, status_code=201)
async def create_site(
    payload: SiteCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    site = Site(
        osm_type=payload.osm_type,
        osm_id=payload.osm_id,
        name=payload.name,
        name_en=payload.name_en,
        name_ar=payload.name_ar,
        details=payload.details,
        categories=payload.categories,
        site_type=payload.site_type,
        geometry=func.ST_SetSRID(func.ST_MakePoint(payload.lon, payload.lat), 4326)
    )
    session.add(site)
    await session.commit()
    await session.refresh(site)
    logger.info("Site created", id=str(site.id), name=site.name)
    return SiteResponse(
        id=site.id,
        osm_type=site.osm_type,
        osm_id=site.osm_id,
        name=site.name,
        name_en=site.name_en,
        name_ar=site.name_ar,
        details=site.details,
        categories=site.categories,
        site_type=site.site_type,
        lat=payload.lat,
        lon=payload.lon
    )


@admin_router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    payload: SiteUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon")
    ).where(Site.id == site_id)
    result = await session.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")
    site, current_lat, current_lon = row

    update_data = payload.model_dump(exclude_unset=True)
    if "lat" in update_data or "lon" in update_data:
        new_lat = update_data.pop("lat", current_lat)
        new_lon = update_data.pop("lon", current_lon)
        update_data["geometry"] = func.ST_SetSRID(func.ST_MakePoint(new_lon, new_lat), 4326)
        current_lat, current_lon = new_lat, new_lon

    for key, value in update_data.items():
        setattr(site, key, value)

    await session.commit()
    await session.refresh(site)
    logger.info("Site updated", id=str(site.id))
    return SiteResponse(
        id=site.id,
        osm_type=site.osm_type,
        osm_id=site.osm_id,
        name=site.name,
        name_en=site.name_en,
        name_ar=site.name_ar,
        details=site.details,
        categories=site.categories,
        site_type=site.site_type,
        lat=current_lat,
        lon=current_lon
    )


@admin_router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await session.delete(site)
    await session.commit()
    logger.info("Site deleted", id=str(site_id))
