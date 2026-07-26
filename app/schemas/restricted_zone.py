from pydantic import BaseModel, Field, UUID4
from typing import Optional


class RestrictedZoneCreate(BaseModel):
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: str
    zone_type: str = "restricted"
    source: str = "manual"
    geometry: dict


class RestrictedZoneUpdate(BaseModel):
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: Optional[str] = None
    zone_type: Optional[str] = None
    source: Optional[str] = None
    geometry: Optional[dict] = None


class RestrictedZoneResponse(BaseModel):
    id: UUID4
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: str
    zone_type: str
    source: str

    model_config = {"from_attributes": True}
