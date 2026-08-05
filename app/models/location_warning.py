from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base, TimestampMixin, UUIDMixin

class LocationWarning(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "location_warnings"

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    location: Mapped["Site"] = relationship("Site", back_populates="warnings", lazy="selectin")

    __table_args__ = (
        Index("ix_location_warnings_location_id", "location_id"),
        Index("ix_location_warnings_severity", "severity"),
    )
