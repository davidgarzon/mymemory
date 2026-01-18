"""
Prompt Lab API endpoints for managing and testing LLM prompts.
"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.db import get_db
from app.models import PromptBlock
from app.services.prompt_service import get_active_prompt, reset_to_default_prompt, DEFAULT_PROMPT
from app.services.llm_parser import parse_with_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug/prompt", tags=["debug", "prompt"])


class PromptBlockRequest(BaseModel):
    id: Optional[str] = None
    name: str
    content: str
    enabled: bool = True
    order: int = 0


class PromptBlockResponse(BaseModel):
    id: str
    name: str
    content: str
    enabled: bool
    order: int
    updated_at: str

    class Config:
        from_attributes = True


class PromptTestRequest(BaseModel):
    text: str


class PromptTestResponse(BaseModel):
    prompt_used: str
    response: dict
    response_time_ms: float


@router.get("", response_model=List[PromptBlockResponse])
def list_prompt_blocks(db: Session = Depends(get_db)):
    """Get all prompt blocks ordered by order"""
    blocks = db.query(PromptBlock).order_by(PromptBlock.order.asc()).all()
    return [
        PromptBlockResponse(
            id=block.id,
            name=block.name,
            content=block.content,
            enabled=block.enabled,
            order=block.order,
            updated_at=block.updated_at.isoformat(),
        )
        for block in blocks
    ]


@router.post("", response_model=PromptBlockResponse)
def save_prompt_block(
    block_data: PromptBlockRequest,
    db: Session = Depends(get_db),
):
    """Save or update a prompt block"""
    try:
        if block_data.id:
            # Update existing block
            block = db.query(PromptBlock).filter(PromptBlock.id == block_data.id).first()
            if not block:
                raise HTTPException(status_code=404, detail="Prompt block not found")
            
            # Check if name is changing and if it's already taken
            if block.name != block_data.name:
                existing_with_name = db.query(PromptBlock).filter(
                    PromptBlock.name == block_data.name,
                    PromptBlock.id != block_data.id
                ).first()
                if existing_with_name:
                    raise HTTPException(status_code=400, detail=f"Name '{block_data.name}' already exists")
            
            block.name = block_data.name
            block.content = block_data.content
            block.enabled = block_data.enabled
            block.order = block_data.order
        else:
            # Create new block
            # Check if name already exists
            existing = db.query(PromptBlock).filter(PromptBlock.name == block_data.name).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Name '{block_data.name}' already exists")
            
            block = PromptBlock(
                name=block_data.name,
                content=block_data.content,
                enabled=block_data.enabled,
                order=block_data.order,
            )
            db.add(block)
        
        db.commit()
        db.refresh(block)
        
        return PromptBlockResponse(
            id=block.id,
            name=block.name,
            content=block.content,
            enabled=block.enabled,
            order=block.order,
            updated_at=block.updated_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving prompt block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{block_id}")
def delete_prompt_block(block_id: str, db: Session = Depends(get_db)):
    """Delete a prompt block"""
    try:
        block = db.query(PromptBlock).filter(PromptBlock.id == block_id).first()
        if not block:
            raise HTTPException(status_code=404, detail="Prompt block not found")
        
        db.delete(block)
        db.commit()
        
        return {"ok": True, "message": "Prompt block deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting prompt block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
def reset_prompt_blocks(db: Session = Depends(get_db)):
    """Reset prompt blocks to default structure"""
    try:
        reset_to_default_prompt(db)
        return {"ok": True, "message": "Prompt blocks reset to default"}
    except Exception as e:
        logger.error(f"Error resetting prompt blocks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
def get_active_prompt_text(db: Session = Depends(get_db)):
    """Get the active prompt (concatenated enabled blocks)"""
    try:
        prompt = get_active_prompt(db)
        return {
            "prompt": prompt,
            "is_default": prompt == DEFAULT_PROMPT,
        }
    except Exception as e:
        logger.error(f"Error getting active prompt: {e}", exc_info=True)
        return {
            "prompt": DEFAULT_PROMPT,
            "is_default": True,
        }


@router.post("/test", response_model=PromptTestResponse)
def test_prompt(
    request: PromptTestRequest,
    db: Session = Depends(get_db),
):
    """Test the active prompt with a text input"""
    try:
        # Get active prompt
        prompt_used = get_active_prompt(db)
        
        # Measure response time
        start_time = time.time()
        
        # Parse with LLM using active prompt
        result = parse_with_llm(request.text, db=db)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return PromptTestResponse(
            prompt_used=prompt_used,
            response=result,
            response_time_ms=round(response_time_ms, 2),
        )
    except Exception as e:
        logger.error(f"Error testing prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
