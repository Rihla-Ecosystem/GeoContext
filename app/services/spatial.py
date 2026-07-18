import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography

from app.core.config import settings
from app.models.boundary import Boundary
from app.models.site import Site
from app.models.restricted_zone import RestrictedZone
from app.schemas.context import ContextResponse, SiteResult, AreaAdvisory

logger = structlog.get_logger()

async def get_spatial_context(session: AsyncSession, lat: float, lon: float, radius_meters: float) -> ContextResponse:
    """
    Executes the core spatial queries to determine the context of a given (lat, lon) coordinate.
    """
    point_geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    # 1. Egypt boundary check via ST_Contains
    logger.debug("Checking country boundary", lat=lat, lon=lon)
    egypt_query = select(Boundary).where(
        Boundary.level == 'country',
        func.ST_Contains(Boundary.geometry, point_geom)
    ).limit(1)

    egypt_result = await session.execute(egypt_query)
    egypt_boundary = egypt_result.scalars().first()

    # Short-circuit if outside Egypt
    if not egypt_boundary:
        logger.info("Point outside Egypt", lat=lat, lon=lon)
        return ContextResponse(
            in_egypt=False,
            governorate=None,
            at_site=None,
            nearby_sites=[],
            nearby_services=[],
            area_advisories=[]
        )

    # 2. Governorate lookup via ST_Contains
    logger.debug("Checking governorate boundary", lat=lat, lon=lon)
    gov_query = select(Boundary).where(
        Boundary.level == 'governorate',
        func.ST_Contains(Boundary.geometry, point_geom)
    ).limit(1)

    gov_result = await session.execute(gov_query)
    governorate = gov_result.scalars().first()

    gov_name = None
    if governorate:
        gov_name = governorate.name_en if governorate.name_en else governorate.name

    # 3. Nearby tourist sites via ST_DWithin
    logger.debug("Finding nearby tourist sites", lat=lat, lon=lon, radius=radius_meters)
    site_query = select(
        Site,
        func.ST_Distance(
            cast(Site.geometry, Geography),
            cast(point_geom, Geography)
        ).label("distance"),
        func.ST_Y(Site.geometry).label("site_lat"),
        func.ST_X(Site.geometry).label("site_lon")
    ).where(
        Site.site_type == 'tourist',
        func.ST_DWithin(
            cast(Site.geometry, Geography),
            cast(point_geom, Geography),
            radius_meters
        )
    ).order_by("distance")

    site_result = await session.execute(site_query)

    at_site = None
    nearby_sites = []

    for site, distance, site_lat, site_lon in site_result:
        result_obj = SiteResult(
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            categories=site.categories,
            details=site.details,
            distance_meters=round(distance, 2),
            lat=site_lat,
            lon=site_lon
        )
        # Only tourist sites count as "at_site"
        if not at_site and distance <= settings.AT_SITE_RADIUS:
            at_site = result_obj
        else:
            nearby_sites.append(result_obj)

    # 4. Nearby infrastructure/services via ST_DWithin
    logger.debug("Finding nearby services", lat=lat, lon=lon, radius=radius_meters)
    svc_query = select(
        Site,
        func.ST_Distance(
            cast(Site.geometry, Geography),
            cast(point_geom, Geography)
        ).label("distance"),
        func.ST_Y(Site.geometry).label("site_lat"),
        func.ST_X(Site.geometry).label("site_lon")
    ).where(
        Site.site_type == 'infrastructure',
        func.ST_DWithin(
            cast(Site.geometry, Geography),
            cast(point_geom, Geography),
            radius_meters
        )
    ).order_by("distance")

    svc_result = await session.execute(svc_query)

    nearby_services = [
        SiteResult(
            name=site.name,
            name_en=site.name_en,
            name_ar=site.name_ar,
            categories=site.categories,
            details=site.details,
            distance_meters=round(distance, 2),
            lat=site_lat,
            lon=site_lon
        )
        for site, distance, site_lat, site_lon in svc_result
    ]

    # 5. Area advisories via ST_Intersects
    logger.debug("Checking area advisories", lat=lat, lon=lon)
    zone_query = select(RestrictedZone).where(
        func.ST_Intersects(RestrictedZone.geometry, point_geom)
    )
    zone_result = await session.execute(zone_query)

    area_advisories = []
    for zone in zone_result.scalars().all():
        area_advisories.append(AreaAdvisory(
            advisory_type=zone.zone_type,
            name=zone.name,
            subtype=zone.subtype,
            source=zone.source,
            reason=zone.reason
        ))

    logger.info(
        "Spatial context generated",
        lat=lat, lon=lon,
        sites_found=len(nearby_sites),
        services_found=len(nearby_services),
        advisories_found=len(area_advisories)
    )
    return ContextResponse(
        in_egypt=True,
        governorate=gov_name,
        at_site=at_site,
        nearby_sites=nearby_sites,
        nearby_services=nearby_services,
        area_advisories=area_advisories
    )
