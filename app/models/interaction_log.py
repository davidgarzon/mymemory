import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.db import Base


class InteractionLogAction(str, enum.Enum):
    CREATED = "created"
    REMINDED = "reminded"
    DISCUSSED = "discussed"
    POSTPONED = "postponed"
    MERGED = "merged"
    BRIEFING_GENERATED = "briefing_generated"


class InteractionLog(Base):
    __tablename__ = "interaction_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    memory_item_id = Column(
        UUID(as_uuid=True), ForeignKey("memory_item.id"), nullable=True, index=True
    )
    calendar_event_id = Column(
        UUID(as_uuid=True), ForeignKey("calendar_event.id"), nullable=True, index=True
    )
    action = Column(SQLEnum(InteractionLogAction), nullable=False, index=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    memory_item = relationship("MemoryItem", back_populates="interaction_logs")
    calendar_event = relationship("CalendarEvent", back_populates="interaction_logs")
