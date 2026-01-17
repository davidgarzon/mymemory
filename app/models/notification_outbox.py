import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class NotificationChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    PUSH = "push"
    TEST = "test"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False, index=True)
    calendar_event_id = Column(
        UUID(as_uuid=True), ForeignKey("calendar_event.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("person.id"), nullable=False, index=True
    )
    briefing_text = Column(Text, nullable=False)
    push_text = Column(Text, nullable=False)
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    scheduled_for = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    # Relationships
    calendar_event = relationship("CalendarEvent")
    person = relationship("Person")

    __table_args__ = (
        UniqueConstraint('calendar_event_id', 'channel', 'scheduled_for', name='uq_notification_per_event_channel_time'),
    )
