from pydantic import BaseModel, Field, UUID4
from typing import Optional


class NearbySiteResponse(BaseModel):
    id: UUID4
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    categories: list[str]
    details: Optional[dict] = Field(None, description="Detailed JSON content for the site")
    governorate: Optional[str] = Field(None, description="The governorate this site belongs to")
    distance_meters: float
    lat: float
    lon: float


class SiteCreate(BaseModel):
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    details: Optional[dict] = None
    categories: list[str]
    site_type: str = "tourist"
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class SiteUpdate(BaseModel):
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    details: Optional[dict] = None
    categories: Optional[list[str]] = None
    site_type: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class SiteResponse(BaseModel):
    id: UUID4
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    details: Optional[dict] = None
    categories: list[str]
    site_type: str
    lat: float
    lon: float

    model_config = {"from_attributes": True}
