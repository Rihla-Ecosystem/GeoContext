from sqlalchemy import String, BigInteger, UniqueConstraint, Text, Index, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDMixin
from datetime import datetime

class Site(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sites"

    # OSM Identity
    osm_type: Mapped[str] = mapped_column(String(50), nullable=False)
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Core Attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Classification
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="other", index=True)
    site_type: Mapped[str] = mapped_column(String(50), nullable=False, default="tourist", index=True)

    # Geographic context
    governorate: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Egypt")
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Safety & Visibility
    safety_score: Mapped[float] = mapped_column(nullable=True, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="low", index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    visibility: Mapped[str] = mapped_column(String(50), nullable=False, default="public")
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Ownership & Versioning
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    # Spatial
    geometry = mapped_column(
        Geometry(geometry_type='POINT', srid=4326, spatial_index=True),
        nullable=False
    )

    # Relationships
    warnings: Mapped[list["LocationWarning"]] = relationship(
        "LocationWarning",
        foreign_keys="LocationWarning.location_id",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    nearby_services: Mapped[list["NearbyService"]] = relationship(
        "NearbyService",
        foreign_keys="NearbyService.location_id",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_site_osm_identity"),
        Index("ix_sites_categories_gin", "categories", postgresql_using="gin"),
        Index("ix_sites_category", "category"),
        Index("ix_sites_governorate", "governorate"),
        Index("ix_sites_risk_level", "risk_level"),
        Index("ix_sites_status", "status"),
    )
