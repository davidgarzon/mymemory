import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.db import get_db
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus, Person
from app.services.llm_parser import parse_with_llm
from app.services.person_service import get_or_create_person
from app.services.content_normalizer import normalize_content, content_fingerprint
from app.services.semantic_dedup import semantic_dedup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbox", tags=["inbox"])


class InboxRequest(BaseModel):
    text: str
    use_llm: Optional[bool] = True  # Allow frontend to control LLM usage


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


def normalize_llm_response(llm_result: Dict) -> Dict:
    """
    Apply HARD normalization rules to LLM response.
    Backend is the final authority, not the LLM.
    
    Rules applied:
    1. If list_name == "tasks" → type = TASK (TASK overrides LIST_ITEM)
    2. If type == LIST_ITEM and list_name == null → list_name = "shopping"
    3. If type == TASK and list_name == null → list_name = "tasks"
    4. If type == REMINDER → list_name = null
    5. If type == IDEA → list_name = null
    6. If items is empty or invalid → intent = "unknown"
    7. Invalid types are discarded
    """
    intent = llm_result.get("intent", "unknown")
    person = llm_result.get("person")
    items = llm_result.get("items", [])
    
    # Rule 6: If items is empty or not a list → intent = "unknown"
    if not isinstance(items, list) or len(items) == 0:
        return {
            "intent": "unknown",
            "person": None,
            "items": []
        }
    
    # Only normalize if intent is "create_memory"
    if intent != "create_memory":
        return llm_result
    
    normalized_items = []
    valid_types = {"REMINDER", "IDEA", "LIST_ITEM", "TASK"}
    
    for item in items:
        if not isinstance(item, dict):
            continue
        
        # Get and validate type
        item_type = item.get("type", "").upper().strip()
        content = item.get("content", "").strip()
        
        # Rule 7: Discard invalid types or empty content
        if item_type not in valid_types or not content:
            logger.warning(f"Discarding invalid item: type='{item_type}', content='{content[:50]}...'")
            continue
        
        list_name = item.get("list_name")
        # Ensure list_name is a string or None (not an array or other type)
        if isinstance(list_name, (list, tuple)):
            # If LLM returns list_name as array, take first element or use None
            list_name = list_name[0] if len(list_name) > 0 else None
        if list_name and isinstance(list_name, str):
            list_name = list_name.strip()
        elif not isinstance(list_name, str) and list_name is not None:
            # Convert to string if not None and not already string
            try:
                list_name = str(list_name).strip()
            except:
                list_name = None
        
        # Rule 1: TASK overrides LIST_ITEM if list_name == "tasks"
        if list_name == "tasks":
            item_type = "TASK"
            list_name = "tasks"
        
        # Rule 2: LIST_ITEM must have a list_name
        if item_type == "LIST_ITEM" and not list_name:
            list_name = "shopping"
        
        # Rule 3: TASK always belongs to "tasks" list
        if item_type == "TASK" and not list_name:
            list_name = "tasks"
        
        # Rule 4: REMINDER never has list_name
        if item_type == "REMINDER":
            list_name = None
        
        # Rule 5: IDEA never has list_name
        if item_type == "IDEA":
            list_name = None
        
        # Build normalized item
        normalized_item = {
            "type": item_type,
            "content": content,
            "list_name": list_name,
        }
        
        # Preserve related_person_name if present in item (for future extensibility)
        if item.get("related_person_name"):
            normalized_item["related_person_name"] = item["related_person_name"]
        
        normalized_items.append(normalized_item)
    
    # Rule 6 (again): If no valid items after normalization → intent = "unknown"
    if not normalized_items:
        return {
            "intent": "unknown",
            "person": None,
            "items": []
        }
    
    return {
        "intent": intent,
        "person": person,
        "items": normalized_items
    }


def process_multiple_items(db: Session, items_data: List[Dict], original_text: str, person_name: Optional[str] = None) -> InboxResponse:
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
            
            # Determine memory type - LLM returns uppercase types (REMINDER, IDEA, LIST_ITEM, TASK)
            item_type_str = item_data.get("type", "REMINDER").upper()
            if item_type_str == "IDEA":
                memory_type = MemoryItemType.IDEA
            elif item_type_str == "NOTE":
                memory_type = MemoryItemType.NOTE
            elif item_type_str in ("LIST_ITEM", "TASK"):
                # LIST_ITEM and TASK are stored as REMINDER type with list_name
                memory_type = MemoryItemType.REMINDER
            else:
                memory_type = MemoryItemType.REMINDER
            
            # Get or create person if specified (from item or top-level)
            related_person_id = None
            item_person_name = item_data.get("related_person_name") or person_name
            if item_person_name:
                item_person_name = item_person_name.strip()
                if item_person_name and item_person_name.lower() != "comandos":
                    try:
                        person = get_or_create_person(db, item_person_name)
                        related_person_id = person.id
                    except Exception as e:
                        logger.warning(f"Failed to get/create person '{item_person_name}': {e}")
                        related_person_id = None
            
            # Get list_name from normalized item_data (already validated by normalize_llm_response)
            list_name = item_data.get("list_name")  # Can be None for REMINDER/IDEA, or string for LIST_ITEM/TASK
            
            # Normalize content and calculate fingerprint
            normalized_content = normalize_content(content)
            fingerprint = content_fingerprint(normalized_content)
            
            # Step 1: Exact deduplication (fingerprint-based)
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
                # Reuse existing item (exact match)
                memory_item = existing_item
                reused_count += 1
                is_created = False
            else:
                # Step 2: Semantic deduplication (only if exact dedup didn't match)
                # Use original LLM type string (e.g., "LIST_ITEM", "TASK")
                llm_type_str = item_data.get("type", "REMINDER").upper()
                semantic_result = semantic_dedup(
                    db,
                    content=normalized_content,
                    item_type=llm_type_str,
                    list_name=list_name,
                    related_person_id=related_person_id,
                )
                
                # Check if we also need to filter by list_name for semantic matches
                # Since list_name is not stored in MemoryItem, we check it here
                semantic_item = None
                if semantic_result["action"] == "reuse" and semantic_result["matched_item_id"]:
                    semantic_item = db.query(MemoryItem).filter(
                        MemoryItem.id == semantic_result["matched_item_id"]
                    ).first()
                    
                    # Verify list_name matches (both null or both same)
                    # Since list_name is not in DB, we accept the match
                    # Future: could store list_name in MemoryItem or compare differently
                
                if semantic_result["action"] == "reuse" and semantic_item:
                    # Reuse existing item (semantic match)
                    memory_item = semantic_item
                    reused_count += 1
                    is_created = False
                else:
                    # Create new memory item
                    # Calculate embedding for new item
                    from app.services.semantic_dedup import get_embedding
                    embedding = get_embedding(normalized_content)
                    
                    # Determine list_name: only for LIST_ITEM and TASK, None for REMINDER and IDEA
                    stored_list_name = None
                    if item_type_str in ("LIST_ITEM", "TASK"):
                        stored_list_name = list_name
                    else:
                        stored_list_name = None
                    
                    memory_item = MemoryItem(
                        type=memory_type,
                        content=content,
                        normalized_summary=normalized_content,
                        content_fingerprint=fingerprint,
                        related_person_id=related_person_id,
                        list_name=stored_list_name,
                        embedding=embedding,  # Store embedding for future semantic dedup
                        status=MemoryItemStatus.PENDING,
                    )
                    db.add(memory_item)
                    db.flush()  # Flush to get auto-generated values (id, created_at, etc.)
                    created_count += 1
                    is_created = True
            
            # Get person name for response
            item_person_name = None
            if memory_item.related_person:
                item_person_name = memory_item.related_person.display_name
            
            # Return original LLM type in response (LIST_ITEM, TASK, etc.) not internal enum value
            response_type = item_data.get("type", "REMINDER").upper()
            if response_type not in ("REMINDER", "IDEA", "NOTE", "LIST_ITEM", "TASK"):
                response_type = memory_item.type.value.upper()
            
            item_dict = {
                "id": str(memory_item.id),
                "type": response_type,  # Return original LLM type (LIST_ITEM, TASK, etc.)
                "content": memory_item.content,
                "list_name": list_name,
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
    
    # Maintain compatibility: 1 item → memory_item, N items → memory_items
    response_dict = {
        "ok": True,
        "intent": "create_memory",
        "detail": detail_msg,
        "created": created_count > 0,
        "created_count": created_count,
        "reused_count": reused_count,
    }
    
    if len(all_items) == 1:
        # Single item: return both memory_item and memory_items for compatibility
        response_dict["memory_item"] = all_items[0]
        response_dict["memory_items"] = all_items
    else:
        # Multiple items: return only memory_items
        response_dict["memory_items"] = all_items
        response_dict["memory_item"] = None
    
    return InboxResponse(**response_dict)


@router.post("", response_model=InboxResponse)
def process_inbox_text(
    request: InboxRequest,
    db: Session = Depends(get_db),
):
    """Process natural language text from inbox - LLM is the primary authority"""
    logger.info(f"POST /inbox - text='{request.text[:50]}...'")
    
    # Always use LLM as the primary parser (with active prompt from DB)
    llm_result = parse_with_llm(request.text, db=db)
    
    # Apply HARD normalization rules (backend is the final authority)
    normalized_result = normalize_llm_response(llm_result)
    intent = normalized_result.get("intent", "unknown")
    
    if intent == "unknown":
        # LLM didn't understand the message
        return InboxResponse(
            ok=False,
            intent="unknown",
            detail="No he entendido el mensaje. Por favor, intenta con frases como: 'Recuérdame hablar con X de Y' o 'Añade arroz y manzanas'",
            created=False,
            created_count=0,
            reused_count=0,
        )
    
    elif intent == "create_memory":
        # Use normalized result (already validated)
        person_name = normalized_result.get("person")
        items = normalized_result.get("items", [])
        
        # This check should never be true (normalize_llm_response ensures items exist),
        # but we keep it as a safety check
        if not items:
            return InboxResponse(
                ok=False,
                intent=intent,
                detail="No se pudieron extraer items válidos del mensaje",
                created=False,
                created_count=0,
                reused_count=0,
            )
        
        # Process items: person_name applies to all items unless item has its own
        return process_multiple_items(db, items, request.text, person_name=person_name)
    
    else:
        # Any other intent (including create_list_items, list_pending, etc.) → unknown
        return InboxResponse(
            ok=False,
            intent="unknown",
            detail="Intent no soportado. Solo se soporta 'create_memory'",
            created=False,
            created_count=0,
            reused_count=0,
        )
