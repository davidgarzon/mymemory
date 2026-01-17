import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class TestSendRequest(BaseModel):
    text: str


class TestSendResponse(BaseModel):
    ok: bool
    message: str
    response: Optional[dict] = None
    error: Optional[str] = None


@router.post("/test-send", response_model=TestSendResponse)
def test_send_whatsapp(request: TestSendRequest):
    """Send a test WhatsApp message"""
    logger.info(f"POST /whatsapp/test-send - text='{request.text[:50]}...'")
    return TestSendResponse(
        ok=False,
        message="Not implemented yet",
        error="WhatsApp service not implemented",
    )
