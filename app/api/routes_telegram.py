import logging
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


class TestSendRequest(BaseModel):
    text: str


class TestSendResponse(BaseModel):
    ok: bool
    message: str
    response: Optional[dict] = None
    error: Optional[str] = None


@router.post("/test-send", response_model=TestSendResponse)
def test_send_telegram(request: TestSendRequest):
    """Send a test Telegram message"""
    logger.info(f"POST /telegram/test-send - text='{request.text[:50]}...'")
    return TestSendResponse(
        ok=False,
        message="Not implemented yet",
        error="Telegram service not implemented",
    )


@router.post("/webhook/setup")
def setup_telegram_webhook(public_url: Optional[str] = None):
    """Register Telegram webhook URL"""
    logger.info(f"POST /telegram/webhook/setup - public_url={public_url}")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    """Receive updates from Telegram via webhook"""
    logger.info("POST /telegram/webhook received")
    raise HTTPException(status_code=501, detail="Not implemented yet")
