"""Tests for TARepository — uses SQLite in-memory DB."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.models.ta_indicator import TAIndicator
from app.models.ticker import Ticker
from app.repositories.ta_repository import TARepository


@pytest.fixture()
def repo(db):
    return TARepository(db)


def _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 2), sma_20=150.0):
    row = TAIndicator(
        ticker=ticker,
        date=row_date,
        sma_20=sma_20,
        sma_50=None,
        sma_200=None,
        ema_12=None,
        ema_26=None,
        rsi_14=None,
        macd_line=None,
        macd_signal=None,
        macd_hist=None,
        bb_upper=None,
        bb_middle=None,
        bb_lower=None,
        atr_14=None,
        stoch_k=None,
        stoch_d=None,
    )
    db.add(row)
    db.commit()
    return row


def test_get_by_ticker_returns_rows(db, repo):
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 2))
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 3))
    rows = repo.get_by_ticker("AAPL")
    assert len(rows) == 2


def test_get_by_ticker_filters_by_ticker(db, repo):
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 2))
    _insert_ta_row(db, ticker="MSFT", row_date=date(2024, 1, 2))
    rows = repo.get_by_ticker("AAPL")
    assert all(r.ticker == "AAPL" for r in rows)


def test_get_by_ticker_filters_by_date(db, repo):
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 2))
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 10))
    rows = repo.get_by_ticker("AAPL", start_date=date(2024, 1, 5))
    assert len(rows) == 1
    assert rows[0].date == date(2024, 1, 10)


def test_get_latest_returns_most_recent(db, repo):
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 2))
    _insert_ta_row(db, ticker="AAPL", row_date=date(2024, 1, 10))
    row = repo.get_latest("AAPL")
    assert row.date == date(2024, 1, 10)


def test_get_latest_returns_none_when_empty(db, repo):
    row = repo.get_latest("NVDA")
    assert row is None


def test_upsert_many_is_mocked():
    """upsert_many uses PostgreSQL insert — verify interface without hitting DB."""
    mock_db = MagicMock()
    repo = TARepository(mock_db)
    with patch("app.repositories.ta_repository.insert") as mock_insert:
        mock_stmt = MagicMock()
        mock_insert.return_value = mock_stmt
        mock_stmt.values.return_value = mock_stmt
        mock_stmt.on_conflict_do_update.return_value = mock_stmt
        mock_db.execute.return_value.rowcount = 5
        result = repo.upsert_many([{"ticker": "AAPL", "date": date(2024, 1, 2)}])
    assert result == 5
    mock_db.commit.assert_called_once()
