import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.core.db import get_db
from app.models import NotificationOutbox, NotificationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outbox", tags=["outbox"])


class NotificationOutboxResponse(BaseModel):
    id: str
    channel: str
    calendar_event_id: str
    person_id: str
    briefing_text: str
    push_text: str
    status: str
    scheduled_for: str
    created_at: str
    sent_at: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[NotificationOutboxResponse])
def list_outbox(
    status: Optional[NotificationStatus] = None,
    db: Session = Depends(get_db),
):
    """List notifications in outbox"""
    logger.info(f"GET /outbox - status={status}")
    query = db.query(NotificationOutbox)
    if status:
        query = query.filter(NotificationOutbox.status == status)
    notifications = query.order_by(NotificationOutbox.created_at.desc()).all()
    
    return [
        NotificationOutboxResponse(
            id=str(n.id),
            channel=n.channel.value,
            calendar_event_id=str(n.calendar_event_id),
            person_id=str(n.person_id),
            briefing_text=n.briefing_text,
            push_text=n.push_text,
            status=n.status.value,
            scheduled_for=n.scheduled_for.isoformat(),
            created_at=n.created_at.isoformat(),
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
            error=n.error,
        )
        for n in notifications
    ]


@router.post("/{notification_id}/mark-sent", response_model=NotificationOutboxResponse)
def mark_notification_sent(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark a notification as sent"""
    logger.info(f"POST /outbox/{notification_id}/mark-sent")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{notification_id}/send-whatsapp", response_model=NotificationOutboxResponse)
def send_notification_whatsapp(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Send notification via WhatsApp"""
    logger.info(f"POST /outbox/{notification_id}/send-whatsapp")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{notification_id}/send-telegram", response_model=NotificationOutboxResponse)
def send_notification_telegram(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Send notification via Telegram"""
    logger.info(f"POST /outbox/{notification_id}/send-telegram")
    raise HTTPException(status_code=501, detail="Not implemented yet")
