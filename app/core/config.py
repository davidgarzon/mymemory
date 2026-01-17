from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://mymemory:mymemory@localhost:5432/mymemory"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # LLM / Embeddings
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDINGS_MODEL: str = "text-embedding-3-small"
    DEDUP_THRESHOLD: float = 0.70
    DEDUP_TOP_K: int = 5
    DISCUSS_THRESHOLD: float = 0.35
    
    # Google Calendar
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/google/oauth/callback"
    GOOGLE_CALENDAR_ID: str = "primary"
    CALENDAR_SYNC_DAYS: int = 7
    
    # WhatsApp Cloud API
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_TO_PHONE: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v20.0"
    
    # Telegram Bot API
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    TRANSCRIPTION_PROVIDER: str = "openai"
    PUBLIC_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
