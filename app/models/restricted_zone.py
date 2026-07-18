from sqlalchemy import String, BigInteger, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDMixin

class RestrictedZone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "restricted_zones"

    # OSM Identity (Nullable because manual zones don't have them)
    osm_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    osm_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Core Attributes
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification & Sourcing
    subtype: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # military, protected, manual_risk, informal_settlement, etc.
    zone_type: Mapped[str] = mapped_column(String(50), nullable=False, default="restricted", index=True) # restricted, protected, caution
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # osm, manual, etc.

    # Spatial
    geometry = mapped_column(
        Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), 
        nullable=False
    )

    __table_args__ = (
        # A partial index acts as our unique constraint, ensuring we only 
        # enforce uniqueness when osm_id is actually provided (OSM sourced data).
        Index(
            "uq_restricted_zone_osm_identity",
            "osm_type", "osm_id",
            unique=True,
            postgresql_where=(osm_id.is_not(None))
        ),
    )
