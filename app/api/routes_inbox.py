import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.db import get_db

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


@router.post("", response_model=InboxResponse)
def process_inbox_text(
    request: InboxRequest,
    db: Session = Depends(get_db),
):
    """Process natural language text from inbox"""
    logger.info(f"POST /inbox - text='{request.text[:50]}...'")
    return InboxResponse(
        ok=True,
        intent="unknown",
        detail=None,
    )
