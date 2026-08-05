from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography
from typing import List, Optional
import structlog
from shapely.geometry import shape

from app.core.db import get_db
from app.models.boundary import Boundary
from app.schemas.boundary import BoundaryCreate, BoundaryUpdate, BoundaryResponse
from app.core.security import allow_access, require_admin

logger = structlog.get_logger()
router = APIRouter(prefix="/boundaries", tags=["Boundaries"])

_geojson_select = select(
    Boundary,
    func.ST_AsGeoJSON(Boundary.geometry).label("geometry_geojson"),
)


def _row_to_response(boundary: Boundary, geojson: Optional[str]) -> BoundaryResponse:
    geom = None
    if geojson:
        import json as _json
        try:
            geom = _json.loads(geojson)
        except Exception:
            geom = None
    return BoundaryResponse(
        id=boundary.id,
        osm_type=boundary.osm_type,
        osm_id=boundary.osm_id,
        name=boundary.name,
        name_en=boundary.name_en,
        name_ar=boundary.name_ar,
        level=boundary.level,
        geometry_geojson=geom,
        created_at=boundary.created_at,
        updated_at=boundary.updated_at,
    )


@router.get("", response_model=List[BoundaryResponse])
async def list_boundaries(
    level: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    stmt = _geojson_select
    if level:
        stmt = stmt.where(Boundary.level == level)
    stmt = stmt.order_by(Boundary.name)
    result = await session.execute(stmt)
    return [_row_to_response(b, g) for b, g in result.all()]


@router.get("/{boundary_id}", response_model=BoundaryResponse)
async def get_boundary(
    boundary_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    result = await session.execute(_geojson_select.where(Boundary.id == boundary_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Boundary not found")
    boundary, geojson = row
    return _row_to_response(boundary, geojson)


@router.post("", response_model=BoundaryResponse, status_code=201)
async def create_boundary(
    payload: BoundaryCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    geom = shape(payload.geometry)
    ewkt = f"SRID=4326;{geom.wkt}"

    boundary = Boundary(
        osm_type=payload.osm_type,
        osm_id=payload.osm_id,
        name=payload.name,
        name_en=payload.name_en,
        name_ar=payload.name_ar,
        level=payload.level,
        geometry=ewkt
    )
    session.add(boundary)
    await session.commit()
    await session.refresh(boundary)
    logger.info("Boundary created", id=str(boundary.id), name=boundary.name)

    result = await session.execute(
        select(func.ST_AsGeoJSON(Boundary.geometry).label("g")).where(Boundary.id == boundary.id)
    )
    geojson_str = result.scalar()
    return _row_to_response(boundary, geojson_str)


@router.put("/{boundary_id}", response_model=BoundaryResponse)
async def update_boundary(
    boundary_id: str,
    payload: BoundaryUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(_geojson_select.where(Boundary.id == boundary_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Boundary not found")
    boundary, _ = row

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "geometry" in update_data:
        geom = shape(update_data.pop("geometry"))
        update_data["geometry"] = f"SRID=4326;{geom.wkt}"

    for key, value in update_data.items():
        setattr(boundary, key, value)

    await session.commit()
    await session.refresh(boundary)
    logger.info("Boundary updated", id=str(boundary.id))

    result = await session.execute(
        select(func.ST_AsGeoJSON(Boundary.geometry).label("g")).where(Boundary.id == boundary_id)
    )
    geojson_str = result.scalar()
    return _row_to_response(boundary, geojson_str)


@router.delete("/{boundary_id}", status_code=204)
async def delete_boundary(
    boundary_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(select(Boundary).where(Boundary.id == boundary_id))
    boundary = result.scalars().first()
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")
    await session.delete(boundary)
    await session.commit()
    logger.info("Boundary deleted", id=str(boundary_id))
