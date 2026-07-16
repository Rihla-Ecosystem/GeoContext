from sqlalchemy import String, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDMixin

class Boundary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "boundaries"

    # OSM Identity
    osm_type: Mapped[str] = mapped_column(String(50), nullable=False)
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Core Attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Boundary specific
    level: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # e.g. 'country', 'governorate'

    # Spatial
    geometry = mapped_column(
        Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_boundary_osm_identity"),
    )
