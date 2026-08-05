from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime

from pydantic.alias_generators import to_camel
from pydantic import ConfigDict


_camel = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
    from_attributes=True,
)


class RestrictedZoneCreate(BaseModel):
    model_config = _camel
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: str
    zone_type: str = "restricted"
    source: str = "manual"
    geometry: dict


class RestrictedZoneUpdate(BaseModel):
    model_config = _camel
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: Optional[str] = None
    zone_type: Optional[str] = None
    source: Optional[str] = None
    geometry: Optional[dict] = None


class RestrictedZoneResponse(BaseModel):
    model_config = _camel
    id: UUID4
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    reason: Optional[str] = None
    subtype: str
    zone_type: str
    source: str
    geometry_geojson: Optional[dict] = Field(None, alias="geometry_geojson")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
