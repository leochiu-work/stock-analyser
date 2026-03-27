"""Unit tests for TickerRepository (DB session is mocked)."""

from datetime import date
from unittest.mock import MagicMock

from app.repositories.ticker_repository import TickerRepository
from tests.conftest import make_ticker_orm


class TestGetAll:
    def test_returns_all_tickers(self):
        db = MagicMock()
        tickers = [make_ticker_orm("AAPL"), make_ticker_orm("MSFT")]
        db.query.return_value.all.return_value = tickers

        repo = TickerRepository(db)
        result = repo.get_all()

        assert result == tickers

    def test_returns_empty_list_when_no_tickers(self):
        db = MagicMock()
        db.query.return_value.all.return_value = []

        repo = TickerRepository(db)
        assert repo.get_all() == []


class TestUpdateLastFetchDate:
    def test_updates_and_commits(self):
        db = MagicMock()
        ticker = make_ticker_orm("AAPL", last_fetch_date=None)
        db.query.return_value.filter.return_value.first.return_value = ticker

        repo = TickerRepository(db)
        repo.update_last_fetch_date("AAPL", date(2024, 6, 1))

        assert ticker.last_fetch_date == date(2024, 6, 1)
        db.commit.assert_called_once()

    def test_does_nothing_when_ticker_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        repo = TickerRepository(db)
        repo.update_last_fetch_date("UNKNOWN", date(2024, 6, 1))

        db.commit.assert_not_called()

    def test_overwrites_existing_last_fetch_date(self):
        db = MagicMock()
        ticker = make_ticker_orm("AAPL", last_fetch_date=date(2024, 1, 1))
        db.query.return_value.filter.return_value.first.return_value = ticker

        repo = TickerRepository(db)
        repo.update_last_fetch_date("AAPL", date(2024, 6, 1))

        assert ticker.last_fetch_date == date(2024, 6, 1)
