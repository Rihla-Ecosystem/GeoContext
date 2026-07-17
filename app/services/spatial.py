import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography

from app.core.config import settings
from app.models.boundary import Boundary
from app.models.site import Site
from app.models.restricted_zone import RestrictedZone
from app.schemas.context import ContextResponse, SiteResult, ZoneWarning

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
            zone_warnings=[]
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

    # 3. Nearby sites via ST_DWithin
    logger.debug("Finding nearby sites", lat=lat, lon=lon, radius=radius_meters)
    site_query = select(
        Site, 
        func.ST_Distance(
            cast(Site.geometry, Geography), 
            cast(point_geom, Geography)
        ).label("distance"),
        func.ST_Y(Site.geometry).label("site_lat"),
        func.ST_X(Site.geometry).label("site_lon")
    ).where(
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
        # If this is the closest site and it's within AT_SITE_RADIUS, mark it as at_site
        if not at_site and distance <= settings.AT_SITE_RADIUS:
            at_site = result_obj
        else:
            nearby_sites.append(result_obj)
        
    # 4. Restricted zone intersection via ST_Intersects
    logger.debug("Checking restricted zones", lat=lat, lon=lon)
    zone_query = select(RestrictedZone).where(
        func.ST_Intersects(RestrictedZone.geometry, point_geom)
    )
    zone_result = await session.execute(zone_query)
    
    zone_warnings = []
    for zone in zone_result.scalars().all():
        zone_warnings.append(ZoneWarning(
            name=zone.name,
            subtype=zone.subtype,
            source=zone.source,
            reason=zone.reason
        ))
        
    logger.info("Spatial context generated", lat=lat, lon=lon, sites_found=len(nearby_sites), zones_found=len(zone_warnings))
    return ContextResponse(
        in_egypt=True,
        governorate=gov_name,
        at_site=at_site,
        nearby_sites=nearby_sites,
        zone_warnings=zone_warnings
    )
