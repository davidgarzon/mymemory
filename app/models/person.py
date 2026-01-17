import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.db import Base


class Person(Base):
    __tablename__ = "person"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    display_name = Column(String, nullable=False, index=True)
    aliases = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    memory_items = relationship("MemoryItem", back_populates="related_person")

    __table_args__ = (
        UniqueConstraint('display_name', name='uq_person_display_name'),
    )
