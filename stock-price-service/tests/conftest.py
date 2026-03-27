"""Shared fixtures for all test modules."""

from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.stock_price import StockPriceItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_stock_price_orm(
    ticker: str = "AAPL",
    price_date: date = date(2024, 1, 2),
    open_: float = 100.0,
    high: float = 110.0,
    low: float = 90.0,
    close: float = 105.0,
) -> MagicMock:
    """Build a mock ORM StockPrice object."""
    obj = MagicMock()
    obj.ticker = ticker
    obj.date = price_date
    obj.open = open_
    obj.high = high
    obj.low = low
    obj.close = close
    return obj


def make_ticker_orm(
    symbol: str = "AAPL",
    last_fetch_date: date | None = None,
) -> MagicMock:
    obj = MagicMock()
    obj.symbol = symbol
    obj.last_fetch_date = last_fetch_date
    return obj


# ---------------------------------------------------------------------------
# FastAPI test client with overridden DB dependency
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def test_client(mock_db: MagicMock) -> TestClient:
    from app.database import get_db
    from main import app

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
