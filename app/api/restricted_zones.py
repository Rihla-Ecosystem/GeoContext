from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import structlog
from shapely.geometry import shape

from app.core.db import get_db
from app.models.restricted_zone import RestrictedZone
from app.schemas.restricted_zone import RestrictedZoneCreate, RestrictedZoneUpdate, RestrictedZoneResponse
from app.core.security import require_admin

logger = structlog.get_logger()
router = APIRouter(prefix="/restricted-zones", tags=["Restricted Zones"])


@router.get("", response_model=List[RestrictedZoneResponse])
async def list_restricted_zones(
    zone_type: str | None = None,
    subtype: str | None = None,
    session: AsyncSession = Depends(get_db)
):
    query = select(RestrictedZone)
    if zone_type:
        query = query.where(RestrictedZone.zone_type == zone_type)
    if subtype:
        query = query.where(RestrictedZone.subtype == subtype)
    query = query.order_by(RestrictedZone.name)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{zone_id}", response_model=RestrictedZoneResponse)
async def get_restricted_zone(
    zone_id: str,
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(RestrictedZone).where(RestrictedZone.id == zone_id))
    zone = result.scalars().first()
    if not zone:
        raise HTTPException(status_code=404, detail="Restricted zone not found")
    return zone


@router.post("", response_model=RestrictedZoneResponse, status_code=201)
async def create_restricted_zone(
    payload: RestrictedZoneCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
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
    return zone


@router.put("/{zone_id}", response_model=RestrictedZoneResponse)
async def update_restricted_zone(
    zone_id: str,
    payload: RestrictedZoneUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    result = await session.execute(select(RestrictedZone).where(RestrictedZone.id == zone_id))
    zone = result.scalars().first()
    if not zone:
        raise HTTPException(status_code=404, detail="Restricted zone not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "geometry" in update_data:
        geom = shape(update_data.pop("geometry"))
        update_data["geometry"] = f"SRID=4326;{geom.wkt}"

    for key, value in update_data.items():
        setattr(zone, key, value)

    await session.commit()
    await session.refresh(zone)
    logger.info("Restricted zone updated", id=str(zone.id))
    return zone


@router.delete("/{zone_id}", status_code=204)
async def delete_restricted_zone(
    zone_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    result = await session.execute(select(RestrictedZone).where(RestrictedZone.id == zone_id))
    zone = result.scalars().first()
    if not zone:
        raise HTTPException(status_code=404, detail="Restricted zone not found")
    await session.delete(zone)
    await session.commit()
    logger.info("Restricted zone deleted", id=str(zone_id))
