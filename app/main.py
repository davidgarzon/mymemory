import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.core.db import get_db
from app.core.config import settings
from app.api import routes_memory, routes_briefing, routes_inbox, routes_calendar, routes_outbox, routes_whatsapp, routes_telegram

# Log settings for debugging
logger = logging.getLogger(__name__)
logger.info(f"Loaded DEDUP_THRESHOLD: {settings.DEDUP_THRESHOLD}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Second Memory API",
    description="Personal conversational reminder and memory system",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connection"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}",
        )


# Include routers
app.include_router(routes_memory.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_briefing.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_inbox.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_calendar.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_outbox.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_whatsapp.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_telegram.router, prefix=settings.API_V1_PREFIX)

# Mount static files for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    """Root endpoint - redirect to frontend if available"""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "Second Memory API",
        "version": "0.1.0",
        "docs": "/docs",
    }
