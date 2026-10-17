"""
SQLAlchemy database session and engine management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

try:
    from backend.config import settings
except ImportError:
    from config import settings

engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=(settings.app_env == "development_debug"),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session.
    Ensures rollback on error and proper close on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
