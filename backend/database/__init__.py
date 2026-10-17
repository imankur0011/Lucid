"""
Database package for the Intelligent Portfolio Creation backend.
Provides SQLAlchemy engine, session, and Base declarative class.
"""

from backend.database.session import engine, SessionLocal, get_db
from backend.database.base import Base

__all__ = ["engine", "SessionLocal", "get_db", "Base"]
