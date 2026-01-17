import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.db import Base


class MemoryItemType(str, enum.Enum):
    REMINDER = "reminder"
    IDEA = "idea"
    NOTE = "note"


class MemoryItemStatus(str, enum.Enum):
    PENDING = "pending"
    DISCUSSED = "discussed"
    ARCHIVED = "archived"


class MemoryItem(Base):
    __tablename__ = "memory_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(SQLEnum(MemoryItemType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    normalized_summary = Column(Text, nullable=True)
    related_person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"), nullable=True, index=True)
    due_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(MemoryItemStatus), nullable=False, default=MemoryItemStatus.PENDING, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    related_person = relationship("Person", back_populates="memory_items")
    interaction_logs = relationship("InteractionLog", back_populates="memory_item", cascade="all, delete-orphan")
