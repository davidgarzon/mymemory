"""
Briefing API endpoints for preparing and closing meetings with people.

Provides endpoints to:
- Get briefing (pending items) for a person
- Close items after a meeting
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.db import get_db
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus, Person, InteractionLog
from app.models.interaction_log import InteractionLogAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/briefing", tags=["briefing"])


class BriefingResponse(BaseModel):
    person: dict
    pending_items: List[dict]
    recent_discussed: List[dict]


class CloseBriefingRequest(BaseModel):
    item_ids: List[str]


class CloseBriefingResponse(BaseModel):
    closed_count: int


@router.get("/{person_id}", response_model=BriefingResponse)
def get_briefing(
    person_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get briefing (pending items) for a person before a meeting.
    
    Returns:
    - Person info
    - Pending REMINDER items for this person
    - Recently discussed items (last 5)
    """
    # Step 1: Verify person exists
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Step 2: Get pending REMINDER items for this person
    pending_query = db.query(MemoryItem).filter(
        MemoryItem.related_person_id == person_id,
        MemoryItem.status == MemoryItemStatus.PENDING,
        MemoryItem.type == MemoryItemType.REMINDER
    )
    
    # Step 3: Order by semantic_group_id (if exists), then by created_at ASC
    # Items with semantic_group_id first, then by created_at
    pending_items = pending_query.order_by(
        MemoryItem.semantic_group_id.asc().nullslast(),
        MemoryItem.created_at.asc()
    ).all()
    
    # Step 4: Get last 5 DISCUSSED items for this person
    recent_discussed_query = db.query(MemoryItem).filter(
        MemoryItem.related_person_id == person_id,
        MemoryItem.status == MemoryItemStatus.DISCUSSED
    )
    
    # Get InteractionLog to find discussed_at timestamp
    recent_discussed_items = recent_discussed_query.order_by(
        MemoryItem.updated_at.desc()
    ).limit(5).all()
    
    # Build response
    pending_items_data = []
    for item in pending_items:
        pending_items_data.append({
            "id": str(item.id),
            "type": item.type.value.upper(),
            "content": item.content,
            "created_at": item.created_at.isoformat(),
            "semantic_group_id": str(item.semantic_group_id) if item.semantic_group_id else None,
        })
    
    recent_discussed_data = []
    for item in recent_discussed_items:
        # Find the InteractionLog entry for this item (most recent DISCUSSED action)
        interaction_log = db.query(InteractionLog).filter(
            InteractionLog.memory_item_id == item.id,
            InteractionLog.action == InteractionLogAction.DISCUSSED
        ).order_by(InteractionLog.created_at.desc()).first()
        
        discussed_at = interaction_log.created_at.isoformat() if interaction_log else item.updated_at.isoformat()
        
        recent_discussed_data.append({
            "id": str(item.id),
            "content": item.content,
            "discussed_at": discussed_at,
        })
    
    return BriefingResponse(
        person={
            "id": str(person.id),
            "name": person.display_name,
        },
        pending_items=pending_items_data,
        recent_discussed=recent_discussed_data,
    )


@router.post("/{person_id}/close", response_model=CloseBriefingResponse)
def close_briefing(
    person_id: UUID,
    request: CloseBriefingRequest,
    db: Session = Depends(get_db),
):
    """
    Close items after a meeting with a person.
    
    Marks specified items as DISCUSSED and creates InteractionLog entries.
    """
    # Step 1: Verify person exists
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    closed_count = 0
    
    # Step 2: Process each item_id
    for item_id_str in request.item_ids:
        try:
            item_id = UUID(item_id_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid item_id format: {item_id_str}, skipping")
            continue
        
        # Verify item belongs to person and is PENDING
        item = db.query(MemoryItem).filter(
            MemoryItem.id == item_id,
            MemoryItem.related_person_id == person_id,
            MemoryItem.status == MemoryItemStatus.PENDING
        ).first()
        
        if not item:
            logger.warning(f"Item {item_id} not found or not PENDING for person {person_id}, skipping")
            continue
        
        # Step 3: Change status to DISCUSSED
        item.status = MemoryItemStatus.DISCUSSED
        
        # Step 4: Create InteractionLog entry
        interaction_log = InteractionLog(
            memory_item_id=item.id,
            action=InteractionLogAction.DISCUSSED,
            meta={"source": "briefing", "person_name": person.display_name},
        )
        db.add(interaction_log)
        
        closed_count += 1
    
    # Commit all changes
    db.commit()
    
    logger.info(f"Closed {closed_count} items for person {person_id}")
    
    return CloseBriefingResponse(closed_count=closed_count)
