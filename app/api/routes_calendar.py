import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.db import get_db
from app.models import CalendarEvent, MemoryItem, MemoryItemStatus, InteractionLog, InteractionLogAction, Person
from app.services.person_service import get_or_create_person, Person

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


# Keep old Google endpoints for compatibility
@router.get("/google/oauth/start")
def google_oauth_start():
    """Start Google OAuth flow"""
    logger.info("GET /google/oauth/start")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/google/oauth/callback")
def google_oauth_callback():
    """Handle Google OAuth callback"""
    logger.info("GET /google/oauth/callback")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/google/oauth/status")
def google_oauth_status(db: Session = Depends(get_db)):
    """Check Google OAuth status"""
    logger.info("GET /google/oauth/status")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/google/sync")
def sync_calendar(db: Session = Depends(get_db)):
    """Sync calendar events"""
    logger.info("POST /google/sync")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/google/upcoming")
def get_upcoming_events(db: Session = Depends(get_db)):
    """Get upcoming calendar events"""
    logger.info("GET /google/upcoming")
    raise HTTPException(status_code=501, detail="Not implemented yet")


class CreateEventRequest(BaseModel):
    title: str
    start_time: str  # ISO format datetime string
    end_time: str  # ISO format datetime string
    person_name: Optional[str] = None
    provider: str = "manual"
    provider_event_id: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    title: str
    start_time: str
    end_time: str
    person_name: Optional[str] = None


@router.post("/events", response_model=EventResponse)
def create_event(
    request: CreateEventRequest,
    db: Session = Depends(get_db),
):
    """
    Create a calendar event (for testing purposes).
    """
    logger.info(f"POST /calendar/events - title='{request.title}'")
    
    # Parse datetimes
    try:
        start_time = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    
    # Get or create person if specified
    related_person_id = None
    person_name = None
    if request.person_name:
        person = get_or_create_person(db, request.person_name)
        related_person_id = person.id
        person_name = person.display_name
    
    # Generate provider_event_id if not provided
    provider_event_id = request.provider_event_id
    if not provider_event_id:
        import uuid
        provider_event_id = f"{request.provider}_{uuid.uuid4()}"
    
    # Create event
    event = CalendarEvent(
        provider=request.provider,
        provider_event_id=provider_event_id,
        title=request.title,
        start_time=start_time,
        end_time=end_time,
        related_person_id=related_person_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=str(event.id),
        title=event.title,
        start_time=event.start_time.isoformat(),
        end_time=event.end_time.isoformat(),
        person_name=person_name
    )


class BriefingItem(BaseModel):
    id: str
    content: str


class BriefingResponse(BaseModel):
    event_id: str
    person: Optional[str] = None
    briefing: List[BriefingItem] = []


@router.get("/events/{event_id}/briefing", response_model=BriefingResponse)
def get_event_briefing(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get briefing (pending items) for a calendar event.
    
    Returns all PENDING MemoryItems related to the person associated with the event.
    """
    logger.info(f"GET /calendar/events/{event_id}/briefing")
    
    # Find calendar event
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Calendar event {event_id} not found")
    
    # Get person name
    person_name = None
    if event.related_person:
        person_name = event.related_person.display_name
    
    # If no person associated, return empty briefing
    if not event.related_person_id:
        return BriefingResponse(
            event_id=str(event.id),
            person=person_name,
            briefing=[]
        )
    
    # Find pending MemoryItems for this person
    pending_items = db.query(MemoryItem).filter(
        MemoryItem.status == MemoryItemStatus.PENDING,
        MemoryItem.related_person_id == event.related_person_id
    ).order_by(MemoryItem.created_at.desc()).all()
    
    briefing = [
        BriefingItem(
            id=str(item.id),
            content=item.content
        )
        for item in pending_items
    ]
    
    return BriefingResponse(
        event_id=str(event.id),
        person=person_name,
        briefing=briefing
    )


class CloseEventRequest(BaseModel):
    discussed_item_ids: List[str]


class CloseEventResponse(BaseModel):
    ok: bool
    closed: int


@router.post("/events/{event_id}/close", response_model=CloseEventResponse)
def close_event(
    event_id: UUID,
    request: CloseEventRequest,
    db: Session = Depends(get_db),
):
    """
    Mark MemoryItems as DISCUSSED after a meeting.
    
    Associates the items with the calendar event via InteractionLog.
    """
    logger.info(f"POST /calendar/events/{event_id}/close - items: {len(request.discussed_item_ids)}")
    
    # Find calendar event
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Calendar event {event_id} not found")
    
    closed_count = 0
    
    for item_id_str in request.discussed_item_ids:
        try:
            item_id = UUID(item_id_str)
        except ValueError:
            logger.warning(f"Invalid UUID format: {item_id_str}")
            continue
        
        # Find memory item
        memory_item = db.query(MemoryItem).filter(MemoryItem.id == item_id).first()
        if not memory_item:
            logger.warning(f"MemoryItem {item_id} not found")
            continue
        
        # Only close PENDING items
        if memory_item.status != MemoryItemStatus.PENDING:
            logger.info(f"MemoryItem {item_id} is not PENDING (status: {memory_item.status}), skipping")
            continue
        
        # Mark as DISCUSSED
        memory_item.status = MemoryItemStatus.DISCUSSED
        memory_item.updated_at = datetime.utcnow()
        
        # Create interaction log
        interaction_log = InteractionLog(
            memory_item_id=memory_item.id,
            calendar_event_id=event.id,
            action=InteractionLogAction.DISCUSSED,
            meta={"closed_at": datetime.utcnow().isoformat()}
        )
        db.add(interaction_log)
        
        closed_count += 1
    
    db.commit()
    
    logger.info(f"Closed {closed_count} MemoryItems for event {event_id}")
    
    return CloseEventResponse(
        ok=True,
        closed=closed_count
    )
