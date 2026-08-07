from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import structlog

from app.core.db import get_db
from app.core.security import allow_access, require_admin
from app.models.site import Site
from app.models.location_warning import LocationWarning
from app.models.nearby_service import NearbyService
from app.models.boundary import Boundary
from app.models.audit_log import AuditLog
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationListResponse,
    WarningCreate,
    WarningResponse,
    NearbyServiceCreate,
    NearbyServiceResponse,
    BulkStatusRequest,
    BulkDeleteRequest,
    AnalyticsResponse,
    ActivityEventResponse,
    GovernorateResponse,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/locations", tags=["Locations"])

RECENT_WINDOW_HOURS = {"24h": 24, "7d": 24 * 7, "30d": 24 * 30, "90d": 24 * 90}


def _build_location_dict(site: Site, lat: Optional[float] = None, lon: Optional[float] = None) -> dict:
    details = site.details or {}

    warnings_list = [
        {
            "id": str(w.id),
            "title": w.title,
            "severity": w.severity,
            "category": w.category,
            "active": w.active,
            "description": w.description,
            "expires_at": w.expires_at.isoformat() if w.expires_at else None,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in getattr(site, "warnings", []) or []
    ]

    nearby_list = [
        {
            "id": str(s.id),
            "name": s.name,
            "type": s.type,
            "distance_km": s.distance_km,
            "lat": s.lat,
            "lng": s.lng,
            "rating": s.rating,
            "contact": s.contact,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in getattr(site, "nearby_services", []) or []
    ]

    def _details_get(key, default=None):
        return details.get(key, default) if isinstance(details, dict) else default

    return {
        "id": str(site.id),
        "name_en": site.name_en or site.name or "Unnamed",
        "name_ar": site.name_ar,
        "name": site.name,
        "description": site.description,
        "category": site.category,
        "governorate": site.governorate,
        "city": site.city,
        "country": site.country,
        "address": site.address,
        "lat": float(lat) if lat is not None else 0.0,
        "lng": float(lon) if lon is not None else 0.0,
        "safety_score": float(site.safety_score or 0),
        "risk_level": site.risk_level,
        "status": site.status,
        "visibility": site.visibility,
        "ai_summary": site.ai_summary,
        "published_at": site.published_at.isoformat() if site.published_at else None,
        "created_by": site.created_by,
        "updated_by": site.updated_by,
        "version": site.version,
        "created_at": site.created_at.isoformat() if site.created_at else None,
        "updated_at": site.updated_at.isoformat() if site.updated_at else None,
        "details": details,
        "tags": _details_get("tags", []),
        "custom_metadata": _details_get("custom_metadata", {}),
        "interesting_facts": _details_get("interesting_facts", []),
        "ticket": _details_get("ticket"),
        "opening_hours": _details_get("opening_hours", {}),
        "contact": _details_get("contact"),
        "local_laws": _details_get("local_laws"),
        "notes": _details_get("notes"),
        "unesco_status": _details_get("unesco_status"),
        "local_tips": _details_get("local_tips"),
        "drone_rules": _details_get("drone_rules"),
        "photography_rules": _details_get("photography_rules"),
        "accessibility": _details_get("accessibility"),
        "transportation_tips": _details_get("transportation_tips"),
        "emergency_instructions": _details_get("emergency_instructions"),
        "best_time_to_visit": _details_get("best_time_to_visit"),
        "cultural_info": _details_get("cultural_info"),
        "tourist_description": _details_get("tourist_description"),
        "history": _details_get("history"),
        "estimated_duration_minutes": _details_get("estimated_duration_minutes"),
        "documents": _details_get("documents", []),
        "attachments": _details_get("attachments", []),
        "external_links": _details_get("external_links", []),
        "warnings": warnings_list,
        "nearby": nearby_list,
    }


SORT_FIELD_MAP = {
    "nameEn": Site.name_en,
    "name_en": Site.name_en,
    "name": Site.name,
    "safetyScore": Site.safety_score,
    "safety_score": Site.safety_score,
    "category": Site.category,
    "riskLevel": Site.risk_level,
    "risk_level": Site.risk_level,
    "updatedAt": Site.updated_at,
    "updated_at": Site.updated_at,
    "createdAt": Site.created_at,
    "created_at": Site.created_at,
}


def _apply_filters(stmt, search, category, governorate, status, risk, has_warnings, updated_since):
    where_clauses = []
    if search:
        term = f"%{search}%"
        where_clauses.append(
            or_(
                Site.name.ilike(term),
                Site.name_en.ilike(term),
                Site.name_ar.ilike(term),
                Site.governorate.ilike(term),
                Site.city.ilike(term),
                Site.address.ilike(term),
            )
        )
    if category:
        where_clauses.append(Site.category == category)
    if governorate:
        where_clauses.append(Site.governorate == governorate)
    if status:
        where_clauses.append(Site.status == status)
    if risk:
        where_clauses.append(Site.risk_level == risk)
    if updated_since and updated_since in RECENT_WINDOW_HOURS:
        cutoff = datetime.utcnow() - timedelta(hours=RECENT_WINDOW_HOURS[updated_since])
        where_clauses.append(Site.updated_at >= cutoff)

    if where_clauses:
        stmt = stmt.where(and_(*where_clauses))
    if has_warnings is True:
        stmt = stmt.where(
            select(LocationWarning.id)
            .where(
                LocationWarning.location_id == Site.id,
                LocationWarning.active == True,
            )
            .exists()
        )
    elif has_warnings is False:
        stmt = stmt.where(
            ~select(LocationWarning.id)
            .where(
                LocationWarning.location_id == Site.id,
                LocationWarning.active == True,
            )
            .exists()
        )
    return stmt


# ============================================================
# Collection / static routes — defined BEFORE /{location_id}
# ============================================================

@router.get("", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    governorate: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    hasWarnings: Optional[bool] = Query(None),
    updatedSince: Optional[str] = Query(None),
    sortBy: str = Query("updated_at"),
    sortOrder: str = Query("desc"),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    offset = (page - 1) * limit
    sort_col = SORT_FIELD_MAP.get(sortBy, Site.updated_at)
    order_func = asc if sortOrder == "asc" else desc

    stmt = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon"),
    ).options(
        selectinload(Site.warnings),
        selectinload(Site.nearby_services),
    )
    stmt = _apply_filters(stmt, search, category, governorate, status, risk, hasWarnings, updatedSince)
    stmt = stmt.order_by(order_func(sort_col)).offset(offset).limit(limit)

    count_stmt = select(func.count()).select_from(Site)
    count_stmt = _apply_filters(count_stmt, search, category, governorate, status, risk, hasWarnings, updatedSince)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0
    total_pages = max(1, (total + limit - 1) // limit)

    result = await session.execute(stmt)
    rows = result.all()

    locations = []
    for site, lat_val, lon_val in rows:
        loc_dict = _build_location_dict(site, lat_val, lon_val)
        locations.append(loc_dict)

    return LocationListResponse(
        data=locations,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    payload: LocationCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    details = {}
    for field in ["tags", "custom_metadata", "interesting_facts", "ticket", "opening_hours",
                  "contact", "local_laws", "notes", "unesco_status", "local_tips",
                  "drone_rules", "photography_rules", "accessibility", "transportation_tips",
                  "emergency_instructions", "best_time_to_visit", "cultural_info",
                  "tourist_description", "history", "estimated_duration_minutes",
                  "documents", "attachments", "external_links"]:
        details[field] = getattr(payload, field)

    site = Site(
        osm_type="manual",
        osm_id=uuid4().int % (2**63),
        name=payload.name_en or payload.name or "Unnamed",
        name_en=payload.name_en,
        name_ar=payload.name_ar,
        description=payload.description,
        details=details,
        categories=[payload.category] if payload.category else ["other"],
        category=payload.category,
        site_type="tourist",
        governorate=payload.governorate,
        city=payload.city,
        country=payload.country or "Egypt",
        address=payload.address,
        safety_score=payload.safety_score,
        risk_level=payload.risk_level,
        status=payload.status,
        visibility=payload.visibility,
        ai_summary=payload.ai_summary,
        published_at=payload.published_at,
        created_by=user.get("sub", "unknown"),
        updated_by=None,
        version=1,
        geometry=func.ST_SetSRID(func.ST_MakePoint(payload.lng, payload.lat), 4326),
    )
    session.add(site)
    await session.commit()
    await session.refresh(site)
    logger.info("Location created", id=str(site.id), name=site.name)
    return LocationResponse(**_build_location_dict(site, payload.lat, payload.lng))


@router.put("/bulk/status", response_model=dict)
async def bulk_set_status(
    payload: BulkStatusRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    stmt = (
        update(Site)
        .where(Site.id.in_(payload.ids))
        .values(
            status=payload.status,
            updated_by=user.get("sub", "unknown"),
            version=Site.version + 1,
            published_at=datetime.utcnow() if payload.status == "published" else None,
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    updated = result.rowcount
    logger.info("Bulk status update", count=updated, status=payload.status)
    return {"updated": updated}


@router.delete("/bulk", response_model=dict)
async def bulk_delete_locations(
    payload: BulkDeleteRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    stmt = delete(Site).where(Site.id.in_(payload.ids))
    result = await session.execute(stmt)
    await session.commit()
    deleted = result.rowcount
    logger.info("Bulk delete", count=deleted)
    return {"deleted": deleted}


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    total_locations = await session.scalar(select(func.count()).select_from(Site))

    tourist_places = await session.scalar(
        select(func.count()).where(Site.site_type == "tourist")
    )

    restricted_areas = await session.scalar(
        select(func.count()).where(
            or_(Site.category == "restricted", Site.site_type == "infrastructure")
        )
    )

    active_warnings = await session.scalar(
        select(func.count()).select_from(LocationWarning).where(LocationWarning.active == True)
    )

    governorates_result = await session.execute(
        select(Site.governorate).distinct().where(Site.governorate.isnot(None))
    )
    governorate_count = len(governorates_result.scalars().all())

    governorates_all = await session.scalar(
        select(func.count()).select_from(Boundary).where(Boundary.level == "governorate")
    )
    governorates_coverage = round(governorate_count / governorates_all * 100, 1) if governorates_all and governorates_all > 0 else 0.0

    cutoff_30d = datetime.utcnow() - timedelta(days=30)
    recently_updated = await session.scalar(
        select(func.count()).where(Site.updated_at >= cutoff_30d)
    )

    by_category_result = await session.execute(
        select(Site.category, func.count(Site.id)).group_by(Site.category)
    )
    by_category = [{"category": cat, "count": cnt} for cat, cnt in by_category_result.all() if cat]

    by_severity_result = await session.execute(
        select(LocationWarning.severity, func.count(LocationWarning.id))
        .where(LocationWarning.active == True)
        .group_by(LocationWarning.severity)
    )
    warnings_by_severity = [{"severity": sev, "count": cnt} for sev, cnt in by_severity_result.all() if sev]

    top_updated_result = await session.execute(
        select(Site.id, Site.name_en, Site.name, Site.updated_at)
        .where(Site.updated_at.isnot(None))
        .order_by(Site.updated_at.desc())
        .limit(10)
    )
    top_updated = [
         {"id": str(row[0]), "name": row[1] or row[2] or "Unknown", "updatedAt": row[3].isoformat() if row[3] else None}
         for row in top_updated_result.all()
     ]

    return AnalyticsResponse(
        total_locations=total_locations,
        tourist_places=tourist_places,
        restricted_areas=restricted_areas,
        active_warnings=active_warnings,
        governorates_coverage=governorates_coverage,
        recently_updated=recently_updated,
        by_category=by_category,
        warnings_by_severity=warnings_by_severity,
        top_updated=top_updated,
    )


AUDIT_TYPE_MAP = {
    "sites": "location",
    "location_warnings": "warning",
    "restricted_zones": "zone",
    "boundaries": "boundary",
}


@router.get("/activity", response_model=list[ActivityEventResponse])
async def get_activity(
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()

    events = [
        ActivityEventResponse(
            id=str(log.id),
            type=AUDIT_TYPE_MAP.get(log.target_type, "system"),
            action=log.action,
            actor=log.admin_identifier,
            target_id=log.target_id,
            target_name=None,
            created_at=log.created_at.isoformat() if log.created_at else None,
            metadata=log.details,
        )
        for log in logs
    ]

    if not events:
        events = [
            ActivityEventResponse(
                id="welcome",
                type="system",
                action="geocontext_dashboard_activated",
                actor="system",
                created_at=datetime.utcnow().isoformat(),
            )
        ]

    return events


@router.get("/governorates", response_model=list[GovernorateResponse])
async def get_governorates(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    result = await session.execute(
        select(Boundary)
        .where(Boundary.level == "governorate")
        .where(Boundary.name_en.isnot(None))
        .order_by(Boundary.name_en)
    )
    boundaries = result.scalars().all()
    governorates = [
        GovernorateResponse(
            name=b.name_en if b.name_en else b.name,
            name_en=b.name_en,
            name_ar=b.name_ar,
            id=b.id,
        )
        for b in boundaries
    ]
    return governorates


@router.post("/import/geojson", response_model=dict)
async def import_geojson(
    fc: dict,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    features = fc.get("features", [])
    imported = 0
    for feature in features:
        geom = feature.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", [0, 0])
        props = feature.get("properties", {})

        site = Site(
            osm_type="manual",
            osm_id=uuid4().int % (2**63),
            name=props.get("name") or "Imported location",
            name_en=props.get("nameEn"),
            name_ar=props.get("nameAr"),
            description=props.get("description", ""),
            details={
                "tags": props.get("tags", []),
                "custom_metadata": props.get("customMetadata", {}),
                "interesting_facts": props.get("interestingFacts", []),
            },
            categories=[props.get("category", "other")],
            category=props.get("category", "other"),
            site_type="tourist",
            governorate=props.get("governorate", ""),
            city=props.get("city", ""),
            country=props.get("country", "Egypt"),
            address=props.get("address", ""),
            safety_score=props.get("safetyScore", 0),
            risk_level=props.get("riskLevel", "low"),
            status=props.get("status", "draft"),
            visibility=props.get("visibility", "public"),
            published_at=props.get("publishedAt"),
            created_by=user.get("sub", "unknown"),
            version=1,
            geometry=func.ST_SetSRID(func.ST_MakePoint(coords[0], coords[1]), 4326),
        )
        session.add(site)
        imported += 1

    await session.commit()
    logger.info("GeoJSON import", imported=imported)
    return {"imported": imported}


@router.get("/export/geojson", response_model=dict)
async def export_geojson(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    result = await session.execute(
        select(
            Site.id, Site.name_en, Site.name, Site.name_ar, Site.category,
            Site.governorate, Site.city, Site.status, Site.safety_score,
            Site.updated_at,
            func.ST_Y(Site.geometry).label("lat"),
            func.ST_X(Site.geometry).label("lon"),
        )
    )
    features = []
    for row in result.all():
        (site_id, name_en, name, name_ar, category, governorate, city,
         status, safety_score, updated_at, lat, lon) = row
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon or 0), float(lat or 0)]},
            "properties": {
                "id": str(site_id),
                "name": name,
                "nameEn": name_en,
                "nameAr": name_ar,
                "category": category,
                "governorate": governorate,
                "city": city,
                "status": status,
                "safetyScore": float(safety_score or 0),
                "updatedAt": updated_at.isoformat() if updated_at else None,
            },
        })
    return {"type": "FeatureCollection", "name": "rihla-geocontext", "features": features}


# ============================================================
# Location-by-id routes — parameterized, defined AFTER static routes
# ============================================================

@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    stmt = select(
        Site,
        func.ST_Y(Site.geometry).label("lat"),
        func.ST_X(Site.geometry).label("lon"),
    ).options(
        selectinload(Site.warnings),
        selectinload(Site.nearby_services),
    ).where(Site.id == location_id)

    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Location not found")

    site, lat_val, lon_val = row
    return LocationResponse(**_build_location_dict(site, lat_val, lon_val))


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    payload: LocationUpdate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    details_fields = [
        "tags", "custom_metadata", "interesting_facts", "ticket", "opening_hours",
        "contact", "local_laws", "notes", "unesco_status", "local_tips",
        "drone_rules", "photography_rules", "accessibility", "transportation_tips",
        "emergency_instructions", "best_time_to_visit", "cultural_info",
        "tourist_description", "history", "estimated_duration_minutes",
        "documents", "attachments", "external_links",
    ]

    current_details = dict(site.details) if site.details else {}
    new_details = {}
    for field in details_fields:
        if field in update_data:
            new_details[field] = update_data.pop(field)
    if new_details:
        current_details.update(new_details)
        site.details = current_details

    if "name_en" in update_data:
        site.name_en = update_data.pop("name_en")
    if "name_ar" in update_data:
        site.name_ar = update_data.pop("name_ar")
    if "name" in update_data:
        site.name = update_data.pop("name")

    lat = update_data.pop("lat", None)
    lon = update_data.pop("lng", None)
    if lat is not None or lon is not None:
        curr_result = await session.execute(
            select(func.ST_X(Site.geometry).label("x"), func.ST_Y(Site.geometry).label("y"))
            .where(Site.id == location_id)
        )
        curr_row = curr_result.first()
        if curr_row and lat is not None and lon is not None:
            site.geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        elif curr_row and lat is not None:
            site.geometry = func.ST_SetSRID(func.ST_MakePoint(curr_row[0], lat), 4326)
        elif curr_row and lon is not None:
            site.geometry = func.ST_SetSRID(func.ST_MakePoint(lon, curr_row[1]), 4326)

    for key, value in update_data.items():
        if key in details_fields:
            continue
        setattr(site, key, value)

    site.updated_by = user.get("sub", "unknown")
    site.version = (site.version or 1) + 1

    await session.commit()
    await session.refresh(site)
    logger.info("Location updated", id=str(site.id))

    loc_result = await session.execute(
        select(func.ST_Y(Site.geometry).label("lat"), func.ST_X(Site.geometry).label("lon"))
        .where(Site.id == site.id)
    )
    loc_row = loc_result.first()
    lat_val, lon_val = (loc_row[0], loc_row[1]) if loc_row else (None, None)
    return LocationResponse(**_build_location_dict(site, lat_val, lon_val))


@router.delete("/{location_id}", status_code=204)
async def delete_location(
    location_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    await session.delete(site)
    await session.commit()
    logger.info("Location deleted", id=str(location_id))


@router.put("/{location_id}/status", response_model=LocationResponse)
async def set_location_status(
    location_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status is required")
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    site.status = status
    site.updated_by = user.get("sub", "unknown")
    site.version = (site.version or 1) + 1
    if status == "published":
        if site.published_at is None:
            site.published_at = datetime.utcnow()
    else:
        site.published_at = None
    await session.commit()
    await session.refresh(site)
    loc_result = await session.execute(
        select(func.ST_Y(Site.geometry).label("lat"), func.ST_X(Site.geometry).label("lon"))
        .where(Site.id == site.id)
    )
    loc_row = loc_result.first()
    lat_val, lon_val = (loc_row[0], loc_row[1]) if loc_row else (None, None)
    return LocationResponse(**_build_location_dict(site, lat_val, lon_val))


# ---- Warnings ----

@router.post("/{location_id}/warnings", response_model=WarningResponse, status_code=201)
async def add_warning(
    location_id: str,
    payload: WarningCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    warning = LocationWarning(
        location_id=site.id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        category=payload.category,
        active=payload.active,
        expires_at=payload.expires_at,
    )
    session.add(warning)
    await session.commit()
    await session.refresh(warning)
    logger.info("Warning added", location_id=str(location_id), warning_id=str(warning.id))
    return WarningResponse(
        id=warning.id,
        title=warning.title,
        severity=warning.severity,
        category=warning.category,
        active=warning.active,
        description=warning.description,
        expires_at=warning.expires_at.isoformat() if warning.expires_at else None,
        created_at=warning.created_at.isoformat() if warning.created_at else None,
    )


@router.get("/{location_id}/warnings", response_model=list[WarningResponse])
async def list_warnings(
    location_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    result = await session.execute(
        select(LocationWarning).where(LocationWarning.location_id == location_id).order_by(LocationWarning.created_at.desc())
    )
    warnings = result.scalars().all()
    return [
        WarningResponse(
            id=w.id,
            title=w.title,
            severity=w.severity,
            category=w.category,
            active=w.active,
            description=w.description,
            expires_at=w.expires_at.isoformat() if w.expires_at else None,
            created_at=w.created_at.isoformat() if w.created_at else None,
        )
        for w in warnings
    ]


@router.delete("/{location_id}/warnings/{warning_id}", status_code=204)
async def delete_warning(
    location_id: str,
    warning_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(
        select(LocationWarning).where(
            LocationWarning.id == warning_id,
            LocationWarning.location_id == location_id,
        )
    )
    warning = result.scalars().first()
    if not warning:
        raise HTTPException(status_code=404, detail="Warning not found")
    await session.delete(warning)
    await session.commit()
    logger.info("Warning deleted", warning_id=str(warning_id))


# ---- Nearby Services ----

@router.post("/{location_id}/nearby-services", response_model=NearbyServiceResponse, status_code=201)
async def add_nearby_service(
    location_id: str,
    payload: NearbyServiceCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    service = NearbyService(
        location_id=site.id,
        name=payload.name,
        type=payload.type,
        distance_km=payload.distance_km,
        lat=payload.lat,
        lng=payload.lng,
        rating=payload.rating,
        contact=payload.contact,
    )
    session.add(service)
    await session.commit()
    await session.refresh(service)
    logger.info("Nearby service added", location_id=str(location_id), service_id=str(service.id))
    return NearbyServiceResponse(
        id=service.id,
        name=service.name,
        type=service.type,
        distance_km=service.distance_km,
        lat=service.lat,
        lng=service.lng,
        rating=service.rating,
        contact=service.contact,
        created_at=service.created_at.isoformat() if service.created_at else None,
    )


@router.get("/{location_id}/nearby-services", response_model=list[NearbyServiceResponse])
async def list_nearby_services(
    location_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(allow_access),
):
    site = await session.get(Site, location_id)
    if not site:
        raise HTTPException(status_code=404, detail="Location not found")
    result = await session.execute(
        select(NearbyService).where(NearbyService.location_id == location_id).order_by(NearbyService.distance_km)
    )
    services = result.scalars().all()
    return [
        NearbyServiceResponse(
            id=s.id,
            name=s.name,
            type=s.type,
            distance_km=s.distance_km,
            lat=s.lat,
            lng=s.lng,
            rating=s.rating,
            contact=s.contact,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in services
    ]


@router.delete("/{location_id}/nearby-services/{service_id}", status_code=204)
async def delete_nearby_service(
    location_id: str,
    service_id: str,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await session.execute(
        select(NearbyService).where(
            NearbyService.id == service_id,
            NearbyService.location_id == location_id,
        )
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Nearby service not found")
    await session.delete(service)
    await session.commit()
    logger.info("Nearby service deleted", service_id=str(service_id))
