from sqlalchemy import String, Float, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base, TimestampMixin, UUIDMixin

class NearbyService(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "nearby_services"

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    location: Mapped["Site"] = relationship("Site", back_populates="nearby_services", lazy="selectin")

    __table_args__ = (
        Index("ix_nearby_services_location_id", "location_id"),
        Index("ix_nearby_services_type", "type"),
    )
