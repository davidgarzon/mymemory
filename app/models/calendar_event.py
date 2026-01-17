import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.db import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider = Column(String, nullable=False, index=True)
    provider_event_id = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    attendees_raw = Column(JSON, nullable=True)
    related_person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    related_person = relationship("Person")
    interaction_logs = relationship("InteractionLog", back_populates="calendar_event")
