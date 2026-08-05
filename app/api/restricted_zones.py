from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import structlog
from shapely.geometry import shape

from app.core.db import get_db
from app.models.restricted_zone import RestrictedZone
from app.schemas.restricted_zone import RestrictedZoneCreate, RestrictedZoneUpdate, RestrictedZoneResponse
from app.core.security import allow_access, require_admin

logger = structlog.get_logger()
router = APIRouter(prefix="/restricted-zones", tags=["Restricted Zones"])

_geojson_select = select(
    RestrictedZone,
    func.ST_AsGeoJSON(RestrictedZone.geometry).label("geometry_geojson"),
)


def _row_to_response(zone: RestrictedZone, geojson: Optional[str]) -> RestrictedZoneResponse:
    import json as _json
    geom = None
    if geojson:
        try:
            geom = _json.loads(geojson)
        except Exception:
            geom = None
    return RestrictedZoneResponse(
        id=zone.id,
        osm_type=zone.osm_type,
        osm_id=zone.osm_id,
        name=zone.name,
        reason=zone.reason,
        subtype=zone.subtype,
        zone_type=zone.zone_type,
        source=zone.source,
        geometry_geojson=geom,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
    )


@router.get("", response_model=List[RestrictedZoneResponse])
async def list_restricted_zones(
    zone_type: Optional[str] = None,
    subtype: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    stmt = _geojson_select
    if zone_type:
        stmt = stmt.where(RestrictedZone.zone_type == zone_type)
    if subtype:
        stmt = stmt.where(RestrictedZone.subtype == subtype)
    stmt = stmt.order_by(RestrictedZone.name)
    result = await session.execute(stmt)
    return [_row_to_response(z, g) for z, g in result.all()]


@router.get("/{zone_id}", response_model=RestrictedZoneResponse)
async def get_restricted_zone(
    zone_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    result = await session.execute(_geojson_select.where(RestrictedZone.id == zone_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Restricted zone not found")
    zone, geojson = row
    return _row_to_response(zone, geojson)


@router.post("", response_model=RestrictedZoneResponse, status_code=201)
async def create_restricted_zone(
    payload: RestrictedZoneCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    geom = shape(payload.geometry)
    ewkt = f"SRID=4326;{geom.wkt}"

    zone = RestrictedZone(
        osm_type=payload.osm_type,
        osm_id=payload.osm_id,
        name=payload.name,
        reason=payload.reason,
        subtype=payload.subtype,
        zone_type=payload.zone_type,
        source=payload.source,
        geometry=ewkt
    )
    session.add(zone)
    await session.commit()
    await session.refresh(zone)
    logger.info("Restricted zone created", id=str(zone.id), name=zone.name)

    result = await session.execute(
        select(func.ST_AsGeoJSON(RestrictedZone.geometry).label("g")).where(RestrictedZone.id == zone.id)
    )
    geojson_str = result.scalar()
    return _row_to_response(zone, geojson_str)


@router.put("/{zone_id}", response_model=RestrictedZoneResponse)
async def update_restricted_zone(
    zone_id: str,
    payload: RestrictedZoneUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(_geojson_select.where(RestrictedZone.id == zone_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Restricted zone not found")
    zone, _ = row

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "geometry" in update_data:
        geom = shape(update_data.pop("geometry"))
        update_data["geometry"] = f"SRID=4326;{geom.wkt}"

    for key, value in update_data.items():
        setattr(zone, key, value)

    await session.commit()
    await session.refresh(zone)
    logger.info("Restricted zone updated", id=str(zone.id))

    result = await session.execute(
        select(func.ST_AsGeoJSON(RestrictedZone.geometry).label("g")).where(RestrictedZone.id == zone_id)
    )
    geojson_str = result.scalar()
    return _row_to_response(zone, geojson_str)


@router.delete("/{zone_id}", status_code=204)
async def delete_restricted_zone(
    zone_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(select(RestrictedZone).where(RestrictedZone.id == zone_id))
    zone = result.scalars().first()
    if not zone:
        raise HTTPException(status_code=404, detail="Restricted zone not found")
    await session.delete(zone)
    await session.commit()
    logger.info("Restricted zone deleted", id=str(zone_id))
