"""
conftest.py — Shared pytest fixtures.

Uses an in-memory SQLite database so tests run without PostgreSQL.
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test database and uploads dir BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Create temp uploads directory for tests
test_upload_dir = tempfile.mkdtemp(prefix="test_uploads_")
os.environ["UPLOAD_DIR"] = test_upload_dir

# Mock TheDogAPI BEFORE importing app modules
import sys
from unittest.mock import AsyncMock

# Create mock the_dog_api module
mock_the_dog_api = type(sys)('mock_the_dog_api')
mock_the_dog_api.search_the_dog_api = AsyncMock(return_value=[])
sys.modules['app.utils.the_dog_api'] = mock_the_dog_api

from fastapi.testclient import TestClient
from app.database import Base, get_db, get_engine
from app.main import app

# ── In-memory SQLite for tests (no Docker needed) ───────────
SQLALCHEMY_TEST_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Clear settings cache so DATABASE_URL env var is picked up
from app.config import get_settings
get_settings.cache_clear()

# Create fresh engine for tests using test URL
test_engine = get_engine(database_url=SQLALCHEMY_TEST_URL)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# Override get_db dependency for tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """Raw DB session for direct CRUD testing."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up tables after each test."""
    yield
    # Clean up data but keep tables
    from app import models
    session = TestingSession()
    try:
        session.query(models.AdoptionRequest).delete()
        session.query(models.PetPhoto).delete()
        session.query(models.Pet).delete()
        session.query(models.Customer).delete()
        session.commit()
    finally:
        session.close()


