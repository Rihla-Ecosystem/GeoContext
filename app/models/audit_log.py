import uuid
from datetime import datetime, timezone
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now, 
        server_default=func.now()
    )

    # Who did it
    admin_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # What they did
    action: Mapped[str] = mapped_column(String(100), nullable=False) # create, update, delete, verify
    target_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # table name or entity type
    target_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Details of changes
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
