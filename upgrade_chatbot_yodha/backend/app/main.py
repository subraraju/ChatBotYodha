"""
FastAPI application entry point.

    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.config import settings
from app.database import engine
from app.models import Base
from app.api import chat, customers, admin

setup_logging("DEBUG" if settings.DEBUG_MODE else "INFO")
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Starting %s backend  (LLM=%s)", settings.COMPANY_NAME, settings.LLM_PROVIDER)

    # Auto-create tables if they don't exist (dev convenience)
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables ensured")
        except Exception as exc:
            logger.warning("Could not connect to database on startup: %s — server will start anyway", exc)

    yield  # ← app runs

    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=f"{settings.COMPANY_NAME} Chatbot API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (optional)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiter enabled: %s", settings.RATE_LIMIT)
except ImportError:
    logger.info("slowapi not installed — rate limiting disabled")

# ── Routers ───────────────────────────────────────────────────────────

app.include_router(chat.router)
app.include_router(customers.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "company": settings.COMPANY_NAME,
        "llm": settings.LLM_PROVIDER,
        "database": "connected" if engine else "not configured",
    }
