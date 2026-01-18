"""
Semantic deduplication service for MemoryItems.

This service decides if a new item is semantically similar to existing items
using embeddings and cosine similarity.
"""
import logging
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import numpy as np
from openai import OpenAI

from app.core.config import settings
from app.models import MemoryItem, MemoryItemType, MemoryItemStatus
from app.services.content_normalizer import normalize_content

logger = logging.getLogger(__name__)

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client for embeddings"""
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, semantic dedup disabled")
            return None
        try:
            _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    return _openai_client


def get_embedding(text: str) -> Optional[list]:
    """
    Get embedding for text using OpenAI.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats (embedding vector) or None if error
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        response = client.embeddings.create(
            model=settings.EMBEDDINGS_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}", exc_info=True)
        return None


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def semantic_dedup(
    db: Session,
    *,
    content: str,
    item_type: str,
    list_name: Optional[str],
    related_person_id: Optional[UUID],
) -> Dict:
    """
    Decide if a new item is semantically duplicate of existing items.
    
    Args:
        db: Database session
        content: Item content text
        item_type: Item type (e.g., "REMINDER", "LIST_ITEM")
        list_name: Optional list name (for LIST_ITEM/TASK)
        related_person_id: Optional related person ID
        
    Returns:
        {
            "decision": "reuse_pending" | "already_discussed" | "create_new",
            "matched_item": MemoryItem | None,
            "matched_item_id": UUID | None,
            "score": float | None
        }
    """
    # Step 1: Normalize content
    normalized_content = normalize_content(content)
    if not normalized_content:
        logger.warning(f"Empty normalized content for semantic dedup: '{content}'")
        return {
            "decision": "create_new",
            "matched_item": None,
            "matched_item_id": None,
            "score": None
        }
    
    # Step 2: Calculate embedding
    embedding = get_embedding(normalized_content)
    if not embedding:
        logger.warning(f"Failed to get embedding for content: '{content[:50]}...'")
        return {
            "decision": "create_new",
            "matched_item": None,
            "matched_item_id": None,
            "score": None
        }
    
    # Step 3: Build query for candidates - must match ALL criteria:
    # - same type (convert LLM type to internal enum)
    if item_type.upper() == "IDEA":
        memory_type = MemoryItemType.IDEA
    elif item_type.upper() == "NOTE":
        memory_type = MemoryItemType.NOTE
    else:
        memory_type = MemoryItemType.REMINDER  # REMINDER, LIST_ITEM, TASK all map to REMINDER
    
    # Base query for matching type, list_name, related_person_id, and embedding
    base_query = db.query(MemoryItem).filter(
        MemoryItem.type == memory_type,
        MemoryItem.embedding.isnot(None)  # Only items with embeddings
    )
    
    # Filter by list_name: both null or both same
    # Ensure list_name is a string or None (not an array or other type)
    if isinstance(list_name, (list, tuple)):
        list_name = list_name[0] if len(list_name) > 0 else None
    if list_name and isinstance(list_name, str):
        list_name = list_name.strip()
        if not list_name:  # Empty string after strip
            list_name = None
    elif not isinstance(list_name, str) and list_name is not None:
        try:
            list_name = str(list_name).strip()
            if not list_name:
                list_name = None
        except:
            list_name = None
    
    # Apply filters for list_name and related_person_id
    if list_name:
        base_query = base_query.filter(MemoryItem.list_name == list_name)
    else:
        base_query = base_query.filter(MemoryItem.list_name.is_(None))
    
    # Filter by related_person_id: both null or both same
    if related_person_id:
        base_query = base_query.filter(MemoryItem.related_person_id == related_person_id)
    else:
        base_query = base_query.filter(MemoryItem.related_person_id.is_(None))
    
    # Step 4: First search in PENDING items
    pending_query = base_query.filter(MemoryItem.status == MemoryItemStatus.PENDING)
    pending_candidates = pending_query.limit(5).all()
    
    # Step 5: Calculate cosine similarity with PENDING candidates
    best_pending_match = None
    best_pending_score = 0.0
    embedding_array = np.array(embedding)
    
    for candidate in pending_candidates:
        if candidate.embedding is None:
            continue
        
        candidate_embedding = list(candidate.embedding)
        score = cosine_similarity(embedding, candidate_embedding)
        
        if score > best_pending_score:
            best_pending_score = score
            best_pending_match = candidate
    
    # If we found a good match in PENDING (>= 0.88), reuse it
    if best_pending_score >= 0.88:
        logger.info(
            f"Semantic dedup: REUSE_PENDING (score={best_pending_score:.3f}) | "
            f"new='{content[:50]}...' | existing='{best_pending_match.content[:50] if best_pending_match else None}...'"
        )
        return {
            "decision": "reuse_pending",
            "matched_item": best_pending_match,
            "matched_item_id": best_pending_match.id if best_pending_match else None,
            "score": best_pending_score
        }
    
    # Step 6: If no good match in PENDING, search in DISCUSSED items (only for REMINDER with person)
    # Only check DISCUSSED if this is a REMINDER with a related_person_id
    if memory_type == MemoryItemType.REMINDER and related_person_id:
        discussed_query = base_query.filter(MemoryItem.status == MemoryItemStatus.DISCUSSED)
        discussed_candidates = discussed_query.limit(5).all()
        
        best_discussed_match = None
        best_discussed_score = 0.0
        
        for candidate in discussed_candidates:
            if candidate.embedding is None:
                continue
            
            candidate_embedding = list(candidate.embedding)
            score = cosine_similarity(embedding, candidate_embedding)
            
            if score > best_discussed_score:
                best_discussed_score = score
                best_discussed_match = candidate
        
        # If we found a good match in DISCUSSED (>= 0.88), block creation
        if best_discussed_score >= 0.88:
            logger.info(
                f"Semantic dedup: ALREADY_DISCUSSED (score={best_discussed_score:.3f}) | "
                f"new='{content[:50]}...' | discussed='{best_discussed_match.content[:50] if best_discussed_match else None}...'"
            )
            return {
                "decision": "already_discussed",
                "matched_item": best_discussed_match,
                "matched_item_id": best_discussed_match.id if best_discussed_match else None,
                "score": best_discussed_score
            }
    
    # Step 7: No match in PENDING or DISCUSSED, create new
    logger.info(
        f"Semantic dedup: CREATE_NEW (pending_score={best_pending_score:.3f} < 0.88) | "
        f"content='{content[:50]}...'"
    )
    
    return {
        "decision": "create_new",
        "matched_item": None,
        "matched_item_id": None,
        "score": None
    }
