from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
import uuid

from app.models.base import Base, TimestampMixin, UUIDMixin

class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    # User submission details
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False) # hazard, inaccuracy
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_site_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sites.id"), nullable=True)

    # Workflow Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True) # pending, verified, rejected
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Spatial representation of the report
    geometry = mapped_column(
        Geometry(geometry_type='POINT', srid=4326, spatial_index=True), 
        nullable=False
    )
