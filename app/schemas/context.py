from pydantic import BaseModel, Field
from typing import List, Optional

class SiteResult(BaseModel):
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    category: str
    description: Optional[str] = None
    distance_meters: float
    lat: float
    lon: float

class ZoneWarning(BaseModel):
    name: Optional[str] = None
    subtype: str
    source: str
    reason: Optional[str] = None

class ContextResponse(BaseModel):
    in_egypt: bool
    governorate: Optional[str] = None
    at_site: Optional[SiteResult] = Field(None, description="The site the user is physically inside or extremely close to.")
    nearby_sites: List[SiteResult] = Field(default_factory=list, description="Sites within the specified radius.")
    zone_warnings: List[ZoneWarning] = Field(default_factory=list, description="Restricted zones intersecting the user's location.")
