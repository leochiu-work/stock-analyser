"""Shared fixtures for the stock-news-service test suite.

Sets DATABASE_URL and FINNHUB_API_KEY environment variables *before* any app
module is imported so that pydantic-settings and SQLAlchemy engine creation
both see the in-memory SQLite URL at import time.
"""

import os
from datetime import datetime

# Must be set before any app imports so pydantic-settings and the SQLAlchemy
# engine pick up the test values at module-import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FINNHUB_API_KEY", "test-api-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import news as _news_model  # noqa: F401 – registers News table
from app.models import ticker as _ticker_model  # noqa: F401 – registers Ticker table


# ---------------------------------------------------------------------------
# SQLite engine (in-memory, shared across the test session)
# ---------------------------------------------------------------------------

# StaticPool ensures all connections (including those from background threads
# used by the FastAPI TestClient) share the exact same in-memory SQLite
# database connection — preventing "no such table" errors.
_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    """Enable foreign-key enforcement for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_tables():
    """Drop and recreate all tables before every test for full isolation."""
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db_session():
    """Provide a SQLAlchemy session backed by the in-memory SQLite engine."""
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with get_db overridden to use the test db_session."""
    from main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_ticker(db_session):
    """Create and return a Ticker(symbol='AAPL') in the test DB."""
    from app.models.ticker import Ticker

    ticker = Ticker(symbol="AAPL")
    db_session.add(ticker)
    db_session.commit()
    db_session.refresh(ticker)
    return ticker


@pytest.fixture()
def sample_news_records():
    """Return a list of 3 news record dicts ready for direct ORM insertion."""
    return [
        {
            "ticker_symbol": "AAPL",
            "finnhub_id": 1001,
            "headline": "Apple Q1 Results",
            "summary": "Apple reports strong Q1 earnings.",
            "source": "Reuters",
            "url": "http://example.com/1001",
            "image": "",
            "category": "company news",
            "published_at": datetime(2024, 1, 15, 10, 0, 0),
        },
        {
            "ticker_symbol": "AAPL",
            "finnhub_id": 1002,
            "headline": "Apple launches new product",
            "summary": "Apple unveils its latest device lineup.",
            "source": "Bloomberg",
            "url": "http://example.com/1002",
            "image": "",
            "category": "company news",
            "published_at": datetime(2024, 2, 10, 9, 0, 0),
        },
        {
            "ticker_symbol": "AAPL",
            "finnhub_id": 1003,
            "headline": "Apple stock drops",
            "summary": "Apple shares fall amid market volatility.",
            "source": "CNBC",
            "url": "http://example.com/1003",
            "image": "",
            "category": "company news",
            "published_at": datetime(2024, 3, 5, 14, 0, 0),
        },
    ]
