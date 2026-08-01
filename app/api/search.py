from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, case
from typing import Optional, List
import structlog

from app.core.db import get_db
from app.models.site import Site
from app.models.boundary import Boundary
from app.schemas.site import NearbySiteResponse
from app.core.security import allow_access

logger = structlog.get_logger()

router = APIRouter(prefix="/search", tags=["Search"])


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=List[NearbySiteResponse])
async def search_sites(
    q: str = Query(..., min_length=1, max_length=200, description="Search query (English or Arabic)"),
    category: Optional[str] = Query(None, description="Filter by site category (e.g. archaeological, islamic, christian)"),
    governorate: Optional[str] = Query(None, description="Filter by governorate name"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access)
):
    term = q.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    like = f"%{_escape_like(term)}%"
    starts = f"{_escape_like(term)}%"

    governorate_name = (
        select(Boundary.name_en)
        .where(
            Boundary.level == 'governorate',
            func.ST_Intersects(Boundary.geometry, Site.geometry),
        )
        .order_by(
            Boundary.name_en.is_not(None).desc(),
            Boundary.name_en,
        )
        .limit(1)
        .correlate(Site)
        .scalar_subquery()
    )

    query = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon"),
        governorate_name.label("governorate_name"),
        case(
            (
                or_(
                    func.lower(Site.name_en) == term.lower(),
                    func.lower(Site.name) == term.lower(),
                ),
                0,
            ),
            (
                or_(
                    func.lower(Site.name_en).like(starts),
                    func.lower(Site.name).like(starts),
                ),
                1,
            ),
            else_=2,
        ).label("relevance"),
    ).where(
        or_(
            Site.name.ilike(like),
            Site.name_en.ilike(like),
            Site.name_ar.ilike(like),
        )
    )

    if category:
        query = query.where(Site.categories.contains([category]))

    if governorate:
        gov_sub = (
            select(Boundary.geometry)
            .where(
                Boundary.level == 'governorate',
                Boundary.name_en.ilike(f"%{_escape_like(governorate)}%"),
            )
            .limit(1)
            .scalar_subquery()
        )
        query = query.where(func.ST_Intersects(Site.geometry, gov_sub))

    query = query.order_by("relevance", Site.name).limit(limit)

    result = await session.execute(query)

    response = []
    for site, site_lat, site_lon, gov_name, _rel in result:
        response.append(NearbySiteResponse(
            id=site.id,
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            categories=site.categories,
            details=site.details,
            governorate=gov_name,
            distance_meters=0.0,
            lat=site_lat,
            lon=site_lon,
        ))

    return response
