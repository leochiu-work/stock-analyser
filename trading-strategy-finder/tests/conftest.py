"""Shared fixtures for all test modules."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, JSON, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.schema import ColumnDefault

from app.database import Base, get_db


# ---------------------------------------------------------------------------
# SQLite in-memory engine (single-connection StaticPool for thread safety)
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _patch_models_for_sqlite():
    """Replace PostgreSQL-specific column types with SQLite-compatible equivalents."""
    from app.models.strategy import Strategy

    # UUID type → String(36)
    Strategy.__table__.c["id"].type = String(36)

    # UUID default returns uuid.UUID objects; SQLite needs plain str
    Strategy.__table__.c["id"].default = ColumnDefault(lambda: str(uuid.uuid4()))

    # JSONB → JSON
    Strategy.__table__.c["raw_output"].type = JSON()


_patch_models_for_sqlite()

# Enable FK enforcement on SQLite connections
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create tables in the in-memory SQLite database
Base.metadata.create_all(bind=engine)


def _get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test isolation: clear all tables before each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_tables():
    """Truncate all DB tables before every test to prevent cross-test data leakage."""
    from sqlalchemy import text
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()


# ---------------------------------------------------------------------------
# Mock ChromaDB collection
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_collection():
    collection = MagicMock()
    collection.count.return_value = 0
    collection.query.return_value = {
        "documents": [["Test document about investing"]],
        "metadatas": [[{"investor": "test", "source": "test.md"}]],
    }
    collection.get.return_value = {
        "ids": ["doc-1"],
        "metadatas": [{"investor": "buffett", "source": "warren_buffett.md"}],
    }
    return collection


# ---------------------------------------------------------------------------
# DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def db() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_client(mock_collection, monkeypatch):
    import app.chroma as chroma_module
    import seed as seed_module

    monkeypatch.setattr(chroma_module, "get_collection", lambda: mock_collection)
    monkeypatch.setattr(seed_module, "seed_if_empty", lambda: None)

    from main import app

    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client

    app.dependency_overrides.clear()
