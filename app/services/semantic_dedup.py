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
            "action": "reuse" | "create",
            "matched_item_id": UUID | None,
            "score": float | None
        }
    """
    # Step 1: Normalize content
    normalized_content = normalize_content(content)
    if not normalized_content:
        logger.warning(f"Empty normalized content for semantic dedup: '{content}'")
        return {
            "action": "create",
            "matched_item_id": None,
            "score": None
        }
    
    # Step 2: Calculate embedding
    embedding = get_embedding(normalized_content)
    if not embedding:
        logger.warning(f"Failed to get embedding for content: '{content[:50]}...'")
        return {
            "action": "create",
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
    
    query = db.query(MemoryItem).filter(
        MemoryItem.type == memory_type,
        MemoryItem.status == MemoryItemStatus.PENDING,
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
    
    if list_name:
        query = query.filter(MemoryItem.list_name == list_name)
    else:
        query = query.filter(MemoryItem.list_name.is_(None))
    
    # Filter by related_person_id: both null or both same
    if related_person_id:
        query = query.filter(MemoryItem.related_person_id == related_person_id)
    else:
        query = query.filter(MemoryItem.related_person_id.is_(None))
    
    # Step 4: Get top K=5 candidates (we'll calculate similarity in Python)
    candidates = query.limit(5).all()
    
    if not candidates:
        logger.info(f"Semantic dedup: No candidates found for content: '{content[:50]}...'")
        return {
            "action": "create",
            "matched_item_id": None,
            "score": None
        }
    
    # Step 5: Calculate cosine similarity with each candidate
    best_match = None
    best_score = 0.0
    
    embedding_array = np.array(embedding)
    
    for candidate in candidates:
        # candidate.embedding is a Vector type from pgvector
        # Use 'is None' instead of boolean check to avoid array ambiguity error
        if candidate.embedding is None:
            continue
        
        # candidate.embedding is a Vector type, convert to list
        candidate_embedding = list(candidate.embedding)
        score = cosine_similarity(embedding, candidate_embedding)
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    # Step 6: Decision by score
    if best_score >= 0.88:
        action = "reuse"
        matched_item_id = best_match.id if best_match else None
        logger.info(
            f"Semantic dedup: REUSE (score={best_score:.3f}) | "
            f"new='{content[:50]}...' | existing='{best_match.content[:50] if best_match else None}...'"
        )
    elif best_score >= 0.75:
        action = "create"  # Below threshold, but log for analysis
        matched_item_id = None
        logger.info(
            f"Semantic dedup: CREATE (score={best_score:.3f} < 0.88) | "
            f"content='{content[:50]}...' | candidate='{best_match.content[:50] if best_match else None}...'"
        )
    else:
        action = "create"
        matched_item_id = None
        logger.info(
            f"Semantic dedup: CREATE (score={best_score:.3f} < 0.75) | "
            f"content='{content[:50]}...'"
        )
    
    return {
        "action": action,
        "matched_item_id": matched_item_id,
        "score": best_score if best_match else None
    }
