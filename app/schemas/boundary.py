from pydantic import BaseModel, Field, UUID4
from typing import Optional


class BoundaryCreate(BaseModel):
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: str
    geometry: dict


class BoundaryUpdate(BaseModel):
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: Optional[str] = None
    geometry: Optional[dict] = None


class BoundaryResponse(BaseModel):
    id: UUID4
    osm_type: str
    osm_id: int
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    level: str

    model_config = {"from_attributes": True}
