"""
SQLAlchemy engine, session factory, and dependency.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

logger = logging.getLogger(__name__)

engine = (
    create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG_MODE,
        connect_args={"connect_timeout": 10},
    )
    if settings.database_configured
    else None
)

SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if engine
    else None
)


def get_db():
    """FastAPI dependency — yields a DB session."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
