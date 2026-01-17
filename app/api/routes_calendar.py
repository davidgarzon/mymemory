import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google", tags=["calendar"])


@router.get("/oauth/start")
def google_oauth_start():
    """Start Google OAuth flow"""
    logger.info("GET /google/oauth/start")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/oauth/callback")
def google_oauth_callback():
    """Handle Google OAuth callback"""
    logger.info("GET /google/oauth/callback")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/oauth/status")
def google_oauth_status(db: Session = Depends(get_db)):
    """Check Google OAuth status"""
    logger.info("GET /google/oauth/status")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/sync")
def sync_calendar(db: Session = Depends(get_db)):
    """Sync calendar events"""
    logger.info("POST /google/sync")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/upcoming")
def get_upcoming_events(db: Session = Depends(get_db)):
    """Get upcoming calendar events"""
    logger.info("GET /google/upcoming")
    raise HTTPException(status_code=501, detail="Not implemented yet")
