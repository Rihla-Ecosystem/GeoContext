from pydantic import BaseModel, Field, UUID4
from typing import Optional

class ReportCreate(BaseModel):
    report_type: str = Field(..., description="Type of report (e.g., hazard, inaccuracy, missing_data)")
    description: str = Field(..., description="Detailed description of the issue")
    severity: Optional[str] = Field(None, description="Severity level (e.g., low, medium, high, critical)")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the report")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the report")
    related_site_id: Optional[UUID4] = Field(None, description="UUID of the related site if applicable")

class ReportResponse(ReportCreate):
    id: UUID4
    status: str
    
    model_config = {
        "from_attributes": True
    }
