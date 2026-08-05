from pydantic import BaseModel, Field, UUID4
from typing import Optional, Any
from datetime import datetime

from pydantic.alias_generators import to_camel
from pydantic import ConfigDict


_camel = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
    from_attributes=True,
)


class BoundaryCreate(BaseModel):
    model_config = _camel
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: str
    geometry: dict


class BoundaryUpdate(BaseModel):
    model_config = _camel
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: Optional[str] = None
    geometry: Optional[dict] = None


class BoundaryResponse(BaseModel):
    model_config = _camel
    id: UUID4
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: str
    geometry_geojson: Optional[dict] = Field(None, alias="geometry_geojson")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
