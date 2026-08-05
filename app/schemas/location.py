from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel


def camel_config() -> ConfigDict:
    """Config that generates camelCase aliases from snake_case field names."""
    return ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class _Base(BaseModel):
    model_config = camel_config()


class WarningSummary(_Base):
    id: UUID
    title: str
    severity: str
    category: str
    active: bool
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class NearbyServiceSummary(_Base):
    id: UUID
    name: str
    type: str
    distance_km: float
    lat: float
    lng: float
    rating: Optional[float] = None
    contact: Optional[str] = None
    created_at: datetime


class LocationResponse(_Base):
    id: UUID
    name_en: str = Field(..., description="Primary English name")
    name_ar: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: str
    governorate: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    lat: float = 0.0
    lng: float = 0.0
    safety_score: float = 0.0
    risk_level: str = "low"
    status: str = "draft"
    visibility: Optional[str] = "public"
    ai_summary: Optional[str] = None
    published_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    details: Optional[dict[str, Any]] = None
    tags: list[str] = []
    custom_metadata: dict[str, str] = {}
    interesting_facts: list[str] = []
    ticket: Optional[dict[str, Any]] = None
    opening_hours: dict[str, Any] = {}
    contact: Optional[dict[str, Any]] = None
    local_laws: Optional[str] = None
    notes: Optional[str] = None
    unesco_status: Optional[str] = None
    local_tips: Optional[str] = None
    drone_rules: Optional[str] = None
    photography_rules: Optional[str] = None
    accessibility: Optional[str] = None
    transportation_tips: Optional[str] = None
    emergency_instructions: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    cultural_info: Optional[str] = None
    tourist_description: Optional[str] = None
    history: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    documents: list[dict[str, Any]] = []
    attachments: list[dict[str, Any]] = []
    external_links: list[dict[str, Any]] = []
    warnings: list[WarningSummary] = []
    nearby: list[NearbyServiceSummary] = []

    @field_serializer("lat", "lng", "safety_score", check_fields=False)
    def serialize_floats(self, v: Any) -> float:
        if v is None:
            return 0.0
        return float(v)


class LocationCreate(_Base):
    name_en: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    category: str = "other"
    governorate: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "Egypt"
    address: Optional[str] = None
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    safety_score: float = Field(0.0, ge=0, le=100)
    risk_level: str = "low"
    status: str = "draft"
    visibility: str = "public"
    ai_summary: Optional[str] = None
    published_at: Optional[datetime] = None
    details: Optional[dict[str, Any]] = None
    tags: list[str] = []
    custom_metadata: dict[str, str] = {}
    interesting_facts: list[str] = []
    ticket: Optional[dict[str, Any]] = None
    opening_hours: dict[str, Any] = {}
    contact: Optional[dict[str, Any]] = None
    local_laws: Optional[str] = None
    notes: Optional[str] = None
    unesco_status: Optional[str] = None
    local_tips: Optional[str] = None
    drone_rules: Optional[str] = None
    photography_rules: Optional[str] = None
    accessibility: Optional[str] = None
    transportation_tips: Optional[str] = None
    emergency_instructions: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    cultural_info: Optional[str] = None
    tourist_description: Optional[str] = None
    history: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    documents: list[dict[str, Any]] = []
    attachments: list[dict[str, Any]] = []
    external_links: list[dict[str, Any]] = []


class LocationUpdate(_Base):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    governorate: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    safety_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    ai_summary: Optional[str] = None
    published_at: Optional[datetime] = None
    details: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    custom_metadata: Optional[dict[str, str]] = None
    interesting_facts: Optional[list[str]] = None
    ticket: Optional[dict[str, Any]] = None
    opening_hours: Optional[dict[str, Any]] = None
    contact: Optional[dict[str, Any]] = None
    local_laws: Optional[str] = None
    notes: Optional[str] = None
    unesco_status: Optional[str] = None
    local_tips: Optional[str] = None
    drone_rules: Optional[str] = None
    photography_rules: Optional[str] = None
    accessibility: Optional[str] = None
    transportation_tips: Optional[str] = None
    emergency_instructions: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    cultural_info: Optional[str] = None
    tourist_description: Optional[str] = None
    history: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    documents: Optional[list[dict[str, Any]]] = None
    attachments: Optional[list[dict[str, Any]]] = None
    external_links: Optional[list[dict[str, Any]]] = None


class LocationListResponse(_Base):
    data: list[LocationResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class WarningCreate(_Base):
    title: str
    description: Optional[str] = None
    severity: str
    category: str
    active: bool = True
    expires_at: Optional[datetime] = None


class WarningResponse(WarningSummary):
    pass


class NearbyServiceCreate(_Base):
    name: str
    type: str
    distance_km: float
    lat: float
    lng: float
    rating: Optional[float] = None
    contact: Optional[str] = None


class NearbyServiceResponse(NearbyServiceSummary):
    pass


class AnalyticsResponse(BaseModel):
    model_config = camel_config()
    total_locations: int
    tourist_places: int
    restricted_areas: int
    active_warnings: int
    governorates_coverage: float
    recently_updated: int
    by_category: list[dict[str, Any]] = []
    warnings_by_severity: list[dict[str, Any]] = []
    top_updated: list[dict[str, Any]] = []


class ActivityEventResponse(BaseModel):
    model_config = camel_config()
    id: str
    type: str
    action: str
    actor: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    created_at: str
    metadata: Optional[dict[str, Any]] = None


class GovernorateResponse(BaseModel):
    model_config = camel_config()
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    id: Optional[UUID] = None


class BulkStatusRequest(BaseModel):
    ids: list[str]
    status: str


class BulkDeleteRequest(BaseModel):
    ids: list[str]
