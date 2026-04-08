from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings
import time
import logging
import os

logger = logging.getLogger(__name__)

settings = get_settings()

_engine = None


def get_engine(retries: int = 10, delay: int = 3, database_url: str = None):
    """Create engine with retry logic for Docker startup timing."""
    global _engine
    if _engine is not None and database_url is None:
        return _engine

    url = database_url or settings.database_url

    # SQLite-specific args
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    for attempt in range(retries):
        try:
            new_engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                connect_args=connect_args,
            )
            # Test connection
            with new_engine.connect():
                pass
            logger.info("Database connected successfully.")
            if database_url is None:
                _engine = new_engine
            return new_engine
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    raise RuntimeError("Could not connect to the database after multiple attempts.")


def get_session_maker():
    """Get session maker bound to current engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


# Lazy initialization - engine created on first access
SessionLocal = get_session_maker()


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency injection for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
