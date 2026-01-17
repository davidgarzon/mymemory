import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.db import get_db
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus, Person
from app.services.intent_parser import parse_intent
from app.services.person_service import get_or_create_person
from app.services.content_normalizer import normalize_content, content_fingerprint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbox", tags=["inbox"])


class InboxRequest(BaseModel):
    text: str


class InboxResponse(BaseModel):
    ok: bool
    intent: str
    detail: Optional[str] = None
    created: bool = False
    created_count: int = 0
    reused_count: int = 0
    memory_item: Optional[dict] = None  # For single item (backward compatibility)
    memory_items: Optional[List[dict]] = None  # For multiple items
    pending_items: Optional[List[dict]] = None


def process_single_item(db: Session, data: Dict, original_text: str, intent: str) -> InboxResponse:
    """Process a single memory item (deterministic parser result)"""
    # Create memory item
    if not data.get("content"):
        return InboxResponse(
            ok=False,
            intent=intent,
            detail="No se pudo extraer el contenido del mensaje",
            created=False,
            created_count=0,
            reused_count=0,
        )
    
    # Determine memory type (default to reminder)
    memory_type = MemoryItemType.REMINDER
    if "idea" in original_text.lower():
        memory_type = MemoryItemType.IDEA
    
    # Get or create person if specified
    # Only create/assign person if explicitly detected in the message
    related_person_id = None
    if data.get("related_person_name"):
        # Skip creating person if name is "Comandos" (common false positive)
        if data["related_person_name"].lower() == "comandos":
            logger.warning(f"Skipping person creation for 'Comandos' (likely false positive)")
            related_person_id = None
        else:
            person = get_or_create_person(db, data["related_person_name"])
            related_person_id = person.id
    
    # Normalize content and calculate fingerprint
    normalized_content = normalize_content(data["content"])
    fingerprint = content_fingerprint(normalized_content)
    
    # Check for existing similar MemoryItem
    existing_query = db.query(MemoryItem).filter(
        MemoryItem.status == MemoryItemStatus.PENDING,
        MemoryItem.content_fingerprint == fingerprint
    )
    
    # Filter by same person (both null or same ID)
    if related_person_id:
        existing_query = existing_query.filter(
            MemoryItem.related_person_id == related_person_id
        )
    else:
        existing_query = existing_query.filter(
            MemoryItem.related_person_id.is_(None)
        )
    
    existing_item = existing_query.first()
    
    if existing_item:
        # Reuse existing item
        memory_item = existing_item
        created = False
        detail_msg = "Ya lo tenía apuntado"
    else:
        # Create new memory item
        memory_item = MemoryItem(
            type=memory_type,
            content=data["content"],
            normalized_summary=normalized_content,
            content_fingerprint=fingerprint,
            related_person_id=related_person_id,
            status=MemoryItemStatus.PENDING,
        )
        db.add(memory_item)
        db.commit()
        db.refresh(memory_item)
        created = True
        detail_msg = None
    
    # Get person name for response
    person_name = None
    if memory_item.related_person:
        person_name = memory_item.related_person.display_name
    
    return InboxResponse(
        ok=True,
        intent=intent,
        detail=detail_msg,
        created=created,
        created_count=1 if created else 0,
        reused_count=1 if not created else 0,
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


def process_multiple_items(db: Session, items_data: List[Dict], original_text: str) -> InboxResponse:
    """Process multiple memory items (LLM parser result)"""
    created_items = []
    reused_items = []
    created_count = 0
    reused_count = 0
    
    for item_data in items_data:
        try:
            # Validate item data
            content = item_data.get("content", "").strip()
            if not content:
                logger.warning(f"Skipping empty item from LLM parser")
                continue
            
            # Determine memory type
            item_type_str = item_data.get("type", "reminder").lower()
            if item_type_str == "idea":
                memory_type = MemoryItemType.IDEA
            elif item_type_str == "note":
                memory_type = MemoryItemType.NOTE
            else:
                memory_type = MemoryItemType.REMINDER
            
            # Get or create person if specified
            related_person_id = None
            person_name = item_data.get("related_person_name")
            if person_name:
                person_name = person_name.strip()
                if person_name and person_name.lower() != "comandos":
                    try:
                        person = get_or_create_person(db, person_name)
                        related_person_id = person.id
                    except Exception as e:
                        logger.warning(f"Failed to get/create person '{person_name}': {e}")
                        related_person_id = None
            
            # Normalize content and calculate fingerprint
            normalized_content = normalize_content(content)
            fingerprint = content_fingerprint(normalized_content)
            
            # Check for existing similar MemoryItem
            existing_query = db.query(MemoryItem).filter(
                MemoryItem.status == MemoryItemStatus.PENDING,
                MemoryItem.content_fingerprint == fingerprint
            )
            
            # Filter by same person (both null or same ID)
            if related_person_id:
                existing_query = existing_query.filter(
                    MemoryItem.related_person_id == related_person_id
                )
            else:
                existing_query = existing_query.filter(
                    MemoryItem.related_person_id.is_(None)
                )
            
            existing_item = existing_query.first()
            
            if existing_item:
                # Reuse existing item
                memory_item = existing_item
                reused_count += 1
                is_created = False
            else:
                # Create new memory item
                memory_item = MemoryItem(
                    type=memory_type,
                    content=content,
                    normalized_summary=normalized_content,
                    content_fingerprint=fingerprint,
                    related_person_id=related_person_id,
                    status=MemoryItemStatus.PENDING,
                )
                db.add(memory_item)
                created_count += 1
                is_created = True
            
            # Get person name for response
            item_person_name = None
            if memory_item.related_person:
                item_person_name = memory_item.related_person.display_name
            
            item_dict = {
                "id": str(memory_item.id),
                "type": memory_item.type.value,
                "content": memory_item.content,
                "related_person_id": str(memory_item.related_person_id) if memory_item.related_person_id else None,
                "related_person_name": item_person_name,
                "status": memory_item.status.value,
                "created_at": memory_item.created_at.isoformat(),
            }
            
            if is_created:
                created_items.append(item_dict)
            else:
                reused_items.append(item_dict)
                
        except Exception as e:
            logger.error(f"Error processing item from LLM: {e}", exc_info=True)
            continue
    
    # Commit all changes
    db.commit()
    
    # Build response
    all_items = created_items + reused_items
    detail_msg = None
    if created_count > 0 and reused_count > 0:
        detail_msg = f"Creados {created_count} items, reutilizados {reused_count}"
    elif created_count > 0:
        detail_msg = f"Creados {created_count} items"
    elif reused_count > 0:
        detail_msg = f"Reutilizados {reused_count} items (ya existían)"
    else:
        detail_msg = "No se crearon items"
    
    return InboxResponse(
        ok=True,
        intent="create_memory",
        detail=detail_msg,
        created=created_count > 0,
        created_count=created_count,
        reused_count=reused_count,
        memory_items=all_items,
    )


@router.post("", response_model=InboxResponse)
def process_inbox_text(
    request: InboxRequest,
    db: Session = Depends(get_db),
):
    """Process natural language text from inbox"""
    logger.info(f"POST /inbox - text='{request.text[:50]}...'")
    
    # Parse intent (hybrid: deterministic + LLM)
    parsed = parse_intent(request.text, use_llm=True)
    intent = parsed["intent"]
    data = parsed["data"]
    
    if intent == "create_memory":
        # Check if we have multiple items (from LLM) or single item (deterministic)
        items_data = data.get("items", [])
        
        if items_data:
            # Multiple items from LLM
            return process_multiple_items(db, items_data, request.text)
        else:
            # Single item from deterministic parser
            return process_single_item(db, data, request.text, intent)
    
    elif intent == "list_pending":
        # List pending items
        query = db.query(MemoryItem).filter(
            MemoryItem.status == MemoryItemStatus.PENDING
        )
        
        # Filter by person if specified
        if data["related_person_name"]:
            try:
                person = get_or_create_person(db, data["related_person_name"])
                query = query.filter(MemoryItem.related_person_id == person.id)
                logger.info(f"Filtering pending items by person: {data['related_person_name']} (id: {person.id})")
            except ValueError:
                logger.info(f"Invalid person name: {data['related_person_name']}")
        
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
