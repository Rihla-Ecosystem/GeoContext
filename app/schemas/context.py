from pydantic import BaseModel, Field
from typing import List, Optional

class SiteResult(BaseModel):
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    categories: list[str]
    details: Optional[dict] = None
    distance_meters: float
    lat: float
    lon: float

class AreaAdvisory(BaseModel):
    advisory_type: str  # restricted, protected, caution
    subtype: str
    # NOTE: identity fields (name, reason, source) are deliberately NOT exposed.
    # Zone identity must never reach the client — only class + subtype for legal
    # guidance mapping.

class ZoneGuidance(BaseModel):
    zone_type: str  # restricted, protected, caution
    distance_meters: float

class ContextResponse(BaseModel):
    in_egypt: bool
    governorate: Optional[str] = None
    at_site: Optional[SiteResult] = Field(None, description="The tourist site the user is physically inside or extremely close to.")
    nearby_sites: List[SiteResult] = Field(default_factory=list, description="Tourist sites within the specified radius.")
    nearby_services: List[SiteResult] = Field(default_factory=list, description="Infrastructure/services within the specified radius (police, embassies, etc.).")
    area_advisories: List[AreaAdvisory] = Field(default_factory=list, description="Restricted zones, protected areas, or caution zones intersecting the user's location. Identity fields are stripped.")
    nearby_zone_guidance: List[ZoneGuidance] = Field(default_factory=list, description="Non-exposing guidance for sensitive zones within the detection radius. Never reveals site identity.")


class ZonePolygon(BaseModel):
    """Anonymous polygon for map rendering. Never exposes name/reason/subtype/source."""
    zone_type: str  # restricted, protected, caution
    severity: str   # critical, warning, info
    geometry: dict  # GeoJSON geometry only (Polygon / MultiPolygon)


class ZonesResponse(BaseModel):
    lat: float
    lon: float
    radius_meters: float
    zones: List[ZonePolygon] = Field(default_factory=list)
