import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.db import get_db
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus, Person
from app.services.intent_parser import parse_intent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbox", tags=["inbox"])


class InboxRequest(BaseModel):
    text: str


class InboxResponse(BaseModel):
    ok: bool
    intent: str
    detail: Optional[str] = None
    created: bool = False
    memory_item: Optional[dict] = None
    pending_items: Optional[List[dict]] = None


def get_or_create_person(db: Session, person_name: str) -> Person:
    """Get existing person or create new one"""
    person_name_clean = person_name.strip()
    
    # Try to find by display_name (case-insensitive)
    person = db.query(Person).filter(
        Person.display_name.ilike(person_name_clean)
    ).first()
    
    if not person:
        # Create new person
        person = Person(display_name=person_name_clean, aliases=[])
        db.add(person)
        db.commit()
        db.refresh(person)
        logger.info(f"Created new person: {person_name_clean}")
    
    return person


@router.post("", response_model=InboxResponse)
def process_inbox_text(
    request: InboxRequest,
    db: Session = Depends(get_db),
):
    """Process natural language text from inbox"""
    logger.info(f"POST /inbox - text='{request.text[:50]}...'")
    
    # Parse intent
    parsed = parse_intent(request.text)
    intent = parsed["intent"]
    data = parsed["data"]
    
    if intent == "create_memory":
        # Create memory item
        if not data["content"]:
            return InboxResponse(
                ok=False,
                intent=intent,
                detail="No se pudo extraer el contenido del mensaje",
                created=False,
            )
        
        # Determine memory type (default to reminder)
        memory_type = MemoryItemType.REMINDER
        if "idea" in request.text.lower():
            memory_type = MemoryItemType.IDEA
        
        # Get or create person if specified
        related_person_id = None
        if data["related_person_name"]:
            person = get_or_create_person(db, data["related_person_name"])
            related_person_id = person.id
        
        # Create memory item
        memory_item = MemoryItem(
            type=memory_type,
            content=data["content"],
            related_person_id=related_person_id,
            status=MemoryItemStatus.PENDING,
        )
        db.add(memory_item)
        db.commit()
        db.refresh(memory_item)
        
        # Get person name for response
        person_name = None
        if memory_item.related_person:
            person_name = memory_item.related_person.display_name
        
        return InboxResponse(
            ok=True,
            intent=intent,
            detail=None,
            created=True,
            memory_item={
                "id": str(memory_item.id),
                "type": memory_item.type.value,
                "content": memory_item.content,
                "related_person_id": str(memory_item.related_person_id) if memory_item.related_person_id else None,
                "related_person_name": person_name,
                "status": memory_item.status.value,
                "created_at": memory_item.created_at.isoformat(),
            },
        )
    
    elif intent == "list_pending":
        # List pending items
        query = db.query(MemoryItem).filter(
            MemoryItem.status == MemoryItemStatus.PENDING
        )
        
        # Filter by person if specified
        if data["related_person_name"]:
            person = db.query(Person).filter(
                Person.display_name.ilike(data["related_person_name"])
            ).first()
            if person:
                query = query.filter(MemoryItem.related_person_id == person.id)
                logger.info(f"Filtering pending items by person: {data['related_person_name']} (id: {person.id})")
            else:
                logger.info(f"Person not found: {data['related_person_name']}")
        
        items = query.order_by(MemoryItem.created_at.desc()).all()
        
        pending_items = [
            {
                "id": str(item.id),
                "type": item.type.value,
                "content": item.content,
                "related_person_id": str(item.related_person_id) if item.related_person_id else None,
                "related_person_name": item.related_person.display_name if item.related_person else None,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
        
        return InboxResponse(
            ok=True,
            intent=intent,
            detail=f"Encontrados {len(pending_items)} items pendientes",
            created=False,
            pending_items=pending_items,
        )
    
    else:
        # Unknown intent
        return InboxResponse(
            ok=False,
            intent="unknown",
            detail="No entendí el mensaje. Prueba con: 'Recuérdame hablar con X de Y' o 'Qué tengo pendiente'",
            created=False,
        )
