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
    name: Optional[str] = None
    subtype: str
    source: str
    reason: Optional[str] = None

class ContextResponse(BaseModel):
    in_egypt: bool
    governorate: Optional[str] = None
    at_site: Optional[SiteResult] = Field(None, description="The tourist site the user is physically inside or extremely close to.")
    nearby_sites: List[SiteResult] = Field(default_factory=list, description="Tourist sites within the specified radius.")
    nearby_services: List[SiteResult] = Field(default_factory=list, description="Infrastructure/services within the specified radius (police, embassies, etc.).")
    area_advisories: List[AreaAdvisory] = Field(default_factory=list, description="Restricted zones, protected areas, or caution zones intersecting the user's location.")
