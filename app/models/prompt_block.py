import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime

from app.core.db import Base


class PromptBlock(Base):
    __tablename__ = "prompt_block"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    order = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
