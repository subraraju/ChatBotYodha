"""
Centralized configuration — all env vars loaded once here.

Usage:
    from app.config import settings
"""

import os
from dataclasses import dataclass
from typing import Optional

from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ first, then parent (upgrade_chatbot_yodha/)
_here = Path(__file__).resolve().parent.parent  # backend/
load_dotenv(_here / ".env")          # backend/.env
load_dotenv(_here.parent / ".env")   # upgrade_chatbot_yodha/.env


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or "").strip()


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    # ── Core ──────────────────────────────────────────────────────────
    COMPANY_NAME: str = _env("COMPANY_NAME", "Contoso")
    DATABASE_URL: str = _env("DATABASE_URL")
    DEBUG_MODE: bool = _env_bool("DEBUG_MODE")
    API_SECRET_KEY: str = _env("API_SECRET_KEY", "change-me")
    RATE_LIMIT: str = _env("RATE_LIMIT", "60/minute")

    # ── LLM ───────────────────────────────────────────────────────────
    LLM_PROVIDER: str = _env("LLM_PROVIDER", "openai").lower()
    OPENAI_API_KEY: str = _env("OPENAI_API_KEY")
    OPENAI_MODEL: str = _env("OPENAI_MODEL", "gpt-4o")
    OLLAMA_BASE_URL: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_CHAT_MODEL: str = _env("OLLAMA_CHAT_MODEL", "llama3.2:1b")

    # ── Embeddings ────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = _env("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    EMBEDDING_FALLBACK: str = _env("EMBEDDING_FALLBACK", "all-MiniLM-L6-v2")

    # ── Email ─────────────────────────────────────────────────────────
    SMTP_SERVER: str = _env("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = _env_int("SMTP_PORT", 587)
    EMAIL_USERNAME: str = _env("SMTP_USERNAME") or _env("EMAIL_USERNAME")
    EMAIL_PASSWORD: str = _env("SMTP_PASSWORD") or _env("EMAIL_PASSWORD")
    FROM_EMAIL: str = _env("FROM_EMAIL") or _env("SMTP_USERNAME") or _env("EMAIL_USERNAME")

    # ── Twilio ────────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = _env("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = _env("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = _env("TWILIO_PHONE_NUMBER")
    TWILIO_WHATSAPP_NUMBER: str = _env("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    # ── Telegram ──────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = _env("TELEGRAM_BOT_TOKEN")

    # ── Azure Blob ────────────────────────────────────────────────────
    STORAGE_BACKEND: str = _env("STORAGE_BACKEND", "local").lower()
    AZURE_STORAGE_CONNECTION_STRING: str = (
        _env("AZURE_BLOB_STORAGE_CONNECTION_STRING") or
        _env("AZURE_STORAGE_CONNECTION_STRING") or
        _env("AZURE_BLOB_CONNECTION_STRING")
    )
    AZURE_STORAGE_CONTAINER_NAME: str = (
        _env("AZURE_BLOB_STORAGE_CONTAINER_NAME") or
        _env("AZURE_STORAGE_CONTAINER_NAME") or
        _env("AZURE_BLOB_CONTAINER_NAME", "chatbot-sessions")
    )
    LOCAL_CHAT_DIR: str = _env("LOCAL_CHAT_DIR", "data/chat_sessions")

    # ── Google Calendar ───────────────────────────────────────────────
    GOOGLE_CALENDAR_CREDENTIALS_FILE: str = _env("GOOGLE_CREDENTIALS_FILE") or _env("GOOGLE_CALENDAR_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: str = _env("GOOGLE_TOKEN_FILE", "token.json")

    # ── Meeting Scheduling ────────────────────────────────────────────
    MEETING_TIMEZONE: str = _env("DEFAULT_TIMEZONE", "Asia/Kolkata")
    TEAMS_MEETING_ENABLED: bool = _env_bool("TEAMS_MEETING_ENABLED")
    MAX_SCHEDULING_ATTEMPTS: int = _env_int("MAX_SCHEDULING_ATTEMPTS", 2)
    EMBEDDING_INDEX_DIR: str = _env("EMBEDDING_INDEX_DIR", "data/index")

    # ── Microsoft Teams ───────────────────────────────────────────────
    MSAL_CLIENT_ID: str = _env("MSAL_CLIENT_ID")
    MSAL_TENANT_ID: str = _env("MSAL_TENANT_ID")
    MSAL_CLIENT_SECRET: str = _env("MSAL_CLIENT_SECRET")

    # ── Meeting Defaults ──────────────────────────────────────────────
    DEFAULT_MEETING_DURATION: int = _env_int("DEFAULT_MEETING_DURATION_MINUTES", 60)
    BUSINESS_HOURS_START: int = _env_int("BUSINESS_HOURS_START", 9)
    BUSINESS_HOURS_END: int = _env_int("BUSINESS_HOURS_END", 17)

    # ── Organizer (receives copies of meeting notifications) ──────────
    ORGANIZER_NAME: str = _env("ORGANIZER_NAME", "Yodha Guy")
    ORGANIZER_EMAIL: str = _env("ORGANIZER_EMAIL") or _env("FROM_EMAIL") or _env("SMTP_USERNAME")
    ORGANIZER_PHONE: str = _env("ORGANIZER_PHONE")

    # ── Derived ───────────────────────────────────────────────────────
    @property
    def smtp_configured(self) -> bool:
        return bool(self.EMAIL_USERNAME and self.EMAIL_PASSWORD)

    @property
    def twilio_configured(self) -> bool:
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN)

    @property
    def telegram_configured(self) -> bool:
        return bool(self.TELEGRAM_BOT_TOKEN)

    @property
    def database_configured(self) -> bool:
        return bool(self.DATABASE_URL)


settings = Settings()
