import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.core.db import get_db
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus, Person

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryItemCreate(BaseModel):
    type: MemoryItemType
    content: str
    related_person_name: Optional[str] = None
    due_at: Optional[str] = None


class MemoryItemResponse(BaseModel):
    id: str
    type: str
    content: str
    related_person_id: Optional[str] = None
    related_person_name: Optional[str] = None
    due_at: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/items", response_model=MemoryItemResponse)
def create_memory_item(
    item: MemoryItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new memory item"""
    logger.info(f"POST /memory/items - type={item.type}, content='{item.content[:50]}...'")
    
    memory_item = MemoryItem(
        type=item.type,
        content=item.content,
        status=MemoryItemStatus.PENDING,
    )
    db.add(memory_item)
    db.commit()
    db.refresh(memory_item)
    
    return MemoryItemResponse(
        id=str(memory_item.id),
        type=memory_item.type.value,
        content=memory_item.content,
        related_person_id=str(memory_item.related_person_id) if memory_item.related_person_id else None,
        status=memory_item.status.value,
        created_at=memory_item.created_at.isoformat(),
    )


@router.get("/items", response_model=List[MemoryItemResponse])
def list_memory_items(
    status: Optional[MemoryItemStatus] = None,
    db: Session = Depends(get_db),
):
    """List memory items, optionally filtered by status"""
    logger.info(f"GET /memory/items - status={status}")
    
    query = db.query(MemoryItem)
    if status:
        query = query.filter(MemoryItem.status == status)
    items = query.order_by(MemoryItem.created_at.desc()).all()
    
    return [
        MemoryItemResponse(
            id=str(item.id),
            type=item.type.value,
            content=item.content,
            related_person_id=str(item.related_person_id) if item.related_person_id else None,
            related_person_name=item.related_person.display_name if item.related_person else None,
            due_at=item.due_at.isoformat() if item.due_at else None,
            status=item.status.value,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]


@router.get("/pending", response_model=List[MemoryItemResponse])
def list_pending_memory_items(
    db: Session = Depends(get_db),
):
    """List pending memory items (alias for /items?status=pending)"""
    logger.info("GET /memory/pending")
    return list_memory_items(status=MemoryItemStatus.PENDING, db=db)
