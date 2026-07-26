from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import structlog
from shapely.geometry import shape

from app.core.db import get_db
from app.models.boundary import Boundary
from app.schemas.boundary import BoundaryCreate, BoundaryUpdate, BoundaryResponse
from app.core.security import require_admin

logger = structlog.get_logger()
router = APIRouter(prefix="/boundaries", tags=["Boundaries"])


@router.get("", response_model=List[BoundaryResponse])
async def list_boundaries(
    level: str | None = None,
    session: AsyncSession = Depends(get_db)
):
    query = select(Boundary)
    if level:
        query = query.where(Boundary.level == level)
    query = query.order_by(Boundary.name)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{boundary_id}", response_model=BoundaryResponse)
async def get_boundary(
    boundary_id: str,
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Boundary).where(Boundary.id == boundary_id))
    boundary = result.scalars().first()
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")
    return boundary


@router.post("", response_model=BoundaryResponse, status_code=201)
async def create_boundary(
    payload: BoundaryCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
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
    return boundary


@router.put("/{boundary_id}", response_model=BoundaryResponse)
async def update_boundary(
    boundary_id: str,
    payload: BoundaryUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    result = await session.execute(select(Boundary).where(Boundary.id == boundary_id))
    boundary = result.scalars().first()
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "geometry" in update_data:
        geom = shape(update_data.pop("geometry"))
        update_data["geometry"] = f"SRID=4326;{geom.wkt}"

    for key, value in update_data.items():
        setattr(boundary, key, value)

    await session.commit()
    await session.refresh(boundary)
    logger.info("Boundary updated", id=str(boundary.id))
    return boundary


@router.delete("/{boundary_id}", status_code=204)
async def delete_boundary(
    boundary_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    result = await session.execute(select(Boundary).where(Boundary.id == boundary_id))
    boundary = result.scalars().first()
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")
    await session.delete(boundary)
    await session.commit()
    logger.info("Boundary deleted", id=str(boundary_id))
