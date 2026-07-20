from sqlalchemy import String, BigInteger, UniqueConstraint, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDMixin

class Site(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sites"

    # OSM Identity
    osm_type: Mapped[str] = mapped_column(String(50), nullable=False)
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Core Attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Classification
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False) # archaeological, christian, islamic, hidden_gem, infrastructure
    site_type: Mapped[str] = mapped_column(String(50), nullable=False, default="tourist", index=True) # tourist, infrastructure

    # Spatial
    geometry = mapped_column(
        Geometry(geometry_type='POINT', srid=4326, spatial_index=True), 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_site_osm_identity"),
        Index("ix_sites_categories_gin", "categories", postgresql_using="gin"),
    )
