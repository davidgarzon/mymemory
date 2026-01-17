import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.core.db import get_db
from app.models import Person, MemoryItem, MemoryItemStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/briefing", tags=["briefing"])


class BriefingResponse(BaseModel):
    person_id: str
    person_name: str
    briefing_text: str
    push_text: Optional[str] = None
    pending_items: list = []


@router.get("/person", response_model=BriefingResponse)
def get_briefing_by_person_name(
    person_name: str,
    db: Session = Depends(get_db),
):
    """Get briefing for a person by name"""
    logger.info(f"GET /briefing/person - person_name={person_name}")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/person/{person_id}", response_model=BriefingResponse)
def get_briefing_by_person_id(
    person_id: UUID,
    db: Session = Depends(get_db),
):
    """Get briefing for a person by ID"""
    logger.info(f"GET /briefing/person/{person_id}")
    raise HTTPException(status_code=501, detail="Not implemented yet")
