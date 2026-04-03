"""Unit tests for TickerRepository using a real SQLite in-memory database."""

from datetime import date

import pytest

from app.models.ticker import Ticker
from app.repositories.ticker_repository import TickerRepository


@pytest.fixture()
def repo():
    return TickerRepository()


class TestGetAll:
    def test_get_all_empty(self, db_session, repo):
        """get_all returns an empty list when no tickers exist."""
        result = repo.get_all(db_session)
        assert result == []

    def test_get_all_returns_all_tickers(self, db_session, repo):
        """get_all returns all ticker rows in the DB."""
        db_session.add(Ticker(symbol="AAPL"))
        db_session.add(Ticker(symbol="MSFT"))
        db_session.commit()

        result = repo.get_all(db_session)

        symbols = {t.symbol for t in result}
        assert symbols == {"AAPL", "MSFT"}


class TestGetOrCreate:
    def test_get_or_create_new(self, db_session, repo):
        """Creates a new Ticker when the symbol does not yet exist."""
        ticker = repo.get_or_create(db_session, "GOOG")

        assert ticker.symbol == "GOOG"
        assert ticker.id is not None
        # Confirm it is persisted
        in_db = db_session.query(Ticker).filter(Ticker.symbol == "GOOG").first()
        assert in_db is not None

    def test_get_or_create_existing(self, db_session, repo):
        """Returns the existing Ticker without creating a duplicate."""
        existing = Ticker(symbol="TSLA")
        db_session.add(existing)
        db_session.commit()
        original_id = existing.id

        result = repo.get_or_create(db_session, "TSLA")

        assert result.id == original_id
        count = db_session.query(Ticker).filter(Ticker.symbol == "TSLA").count()
        assert count == 1


class TestUpdateLastFetchDate:
    def test_update_last_fetch_date(self, db_session, repo):
        """update_last_fetch_date sets the date correctly on an existing ticker."""
        ticker = Ticker(symbol="AMZN")
        db_session.add(ticker)
        db_session.commit()

        updated = repo.update_last_fetch_date(db_session, "AMZN", date(2024, 6, 15))

        assert updated.last_fetch_date == date(2024, 6, 15)
        # Verify the change is persisted in the session
        in_db = db_session.query(Ticker).filter(Ticker.symbol == "AMZN").first()
        assert in_db.last_fetch_date == date(2024, 6, 15)

    def test_update_last_fetch_date_overwrites_existing(self, db_session, repo):
        """update_last_fetch_date replaces a previously set date."""
        ticker = Ticker(symbol="META", last_fetch_date=date(2024, 1, 1))
        db_session.add(ticker)
        db_session.commit()

        repo.update_last_fetch_date(db_session, "META", date(2024, 7, 1))

        in_db = db_session.query(Ticker).filter(Ticker.symbol == "META").first()
        assert in_db.last_fetch_date == date(2024, 7, 1)

    def test_update_last_fetch_date_unknown_symbol_returns_none(self, db_session, repo):
        """update_last_fetch_date returns None when the symbol is not found."""
        result = repo.update_last_fetch_date(db_session, "UNKNOWN", date(2024, 1, 1))
        assert result is None
