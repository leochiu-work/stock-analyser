"""Unit tests for StockPriceRepository (DB session is mocked)."""

from datetime import date
from unittest.mock import MagicMock, call, patch

import pytest

from app.repositories.stock_price_repository import StockPriceRepository
from tests.conftest import make_stock_price_orm


# ---------------------------------------------------------------------------
# upsert_many
# ---------------------------------------------------------------------------

class TestUpsertMany:
    def test_empty_list_returns_zero_without_db_call(self):
        db = MagicMock()
        repo = StockPriceRepository(db)
        assert repo.upsert_many([]) == 0
        db.execute.assert_not_called()

    def test_upsert_executes_and_commits(self):
        db = MagicMock()
        db.execute.return_value.rowcount = 2
        repo = StockPriceRepository(db)

        records = [
            {"ticker": "AAPL", "date": date(2024, 1, 2), "open": 100, "high": 110, "low": 90, "close": 105},
            {"ticker": "AAPL", "date": date(2024, 1, 3), "open": 105, "high": 115, "low": 95, "close": 110},
        ]

        with patch("app.repositories.stock_price_repository.insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            result = repo.upsert_many(records)

        assert result == 2
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_upsert_single_record(self):
        db = MagicMock()
        db.execute.return_value.rowcount = 1
        repo = StockPriceRepository(db)

        records = [{"ticker": "TSLA", "date": date(2024, 6, 1), "open": 200, "high": 210, "low": 195, "close": 205}]

        with patch("app.repositories.stock_price_repository.insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            result = repo.upsert_many(records)

        assert result == 1


# ---------------------------------------------------------------------------
# get_by_ticker
# ---------------------------------------------------------------------------

class TestGetByTicker:
    def _make_query_chain(self, db: MagicMock, items: list, total: int) -> None:
        """Wire up the SQLAlchemy query chain mock."""
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.return_value = total
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = items

    def test_returns_items_and_total(self):
        db = MagicMock()
        item = make_stock_price_orm()
        self._make_query_chain(db, [item], total=1)

        repo = StockPriceRepository(db)
        items, total = repo.get_by_ticker("AAPL")

        assert total == 1
        assert items == [item]

    def test_empty_result(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=0)

        repo = StockPriceRepository(db)
        items, total = repo.get_by_ticker("UNKNOWN")

        assert total == 0
        assert items == []

    def test_filters_applied_for_start_and_end_date(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=0)

        repo = StockPriceRepository(db)
        repo.get_by_ticker(
            "AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        # filter() should have been called 3 times: ticker, start_date, end_date
        query = db.query.return_value
        assert query.filter.call_count == 3

    def test_no_date_filters_calls_filter_once(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=0)

        repo = StockPriceRepository(db)
        repo.get_by_ticker("AAPL")

        query = db.query.return_value
        assert query.filter.call_count == 1

    def test_pagination_offset_and_limit(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=100)

        repo = StockPriceRepository(db)
        repo.get_by_ticker("AAPL", offset=20, limit=10)

        query = db.query.return_value
        query.order_by.return_value.offset.assert_called_once_with(20)
        query.order_by.return_value.offset.return_value.limit.assert_called_once_with(10)

    def test_only_start_date_filter(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=0)

        repo = StockPriceRepository(db)
        repo.get_by_ticker("AAPL", start_date=date(2024, 1, 1))

        query = db.query.return_value
        assert query.filter.call_count == 2  # ticker + start_date

    def test_only_end_date_filter(self):
        db = MagicMock()
        self._make_query_chain(db, [], total=0)

        repo = StockPriceRepository(db)
        repo.get_by_ticker("AAPL", end_date=date(2024, 12, 31))

        query = db.query.return_value
        assert query.filter.call_count == 2  # ticker + end_date
