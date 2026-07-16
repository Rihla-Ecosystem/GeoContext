from pydantic import BaseModel, Field, UUID4
from typing import Optional

class NearbySiteResponse(BaseModel):
    id: UUID4
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    category: str
    description: Optional[str] = None
    details: Optional[str] = Field(None, description="Detailed description of the site")
    governorate: Optional[str] = Field(None, description="The governorate this site belongs to")
    distance_meters: float
    lat: float
    lon: float
