"""Shared fixtures for all test modules."""
import os
import sys

# Provide a dummy DATABASE_URL before any app module is imported
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from main import app


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def test_client(mock_db: MagicMock) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def make_ohlc_records(symbol: str = "AAPL", n: int = 300) -> list[dict]:
    """Generate synthetic OHLC records for testing."""
    from datetime import timedelta
    import random
    random.seed(42)
    records = []
    base_date = date(2024, 1, 2)
    price = 150.0
    for i in range(n):
        change = random.uniform(-3.0, 3.0)
        price = max(10.0, price + change)
        records.append({
            "ticker": symbol,
            "date": (base_date + timedelta(days=i)).isoformat(),
            "open": round(price - 1, 2),
            "high": round(price + 2, 2),
            "low": round(price - 2, 2),
            "close": round(price, 2),
        })
    return records
