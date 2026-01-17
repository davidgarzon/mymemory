import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.core.db import Base


class MemoryItemEmbedding(Base):
    __tablename__ = "memory_item_embedding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_item_id = Column(UUID(as_uuid=True), ForeignKey("memory_item.id"), nullable=False, unique=True, index=True)
    embedding = Column(Vector(1536), nullable=False)  # OpenAI text-embedding-3-small dimension
    embedding_model = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('memory_item_id', name='uq_memory_item_embedding_memory_item_id'),
    )
