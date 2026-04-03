"""Unit tests for NewsRepository using a real SQLite in-memory database.

Data is inserted via the ORM directly to avoid the PostgreSQL-dialect
upsert used by NewsRepository.upsert_many.
"""

from datetime import datetime

import pytest

from app.models.news import News
from app.repositories.news_repository import NewsRepository


@pytest.fixture()
def repo():
    return NewsRepository()


def _insert_news(db_session, **kwargs) -> News:
    """Helper: create and persist a News row with sensible defaults."""
    defaults = {
        "ticker_symbol": "AAPL",
        "headline": "Test headline",
        "summary": None,
        "source": None,
        "url": None,
        "image": None,
        "category": None,
    }
    defaults.update(kwargs)
    news = News(**defaults)
    db_session.add(news)
    db_session.commit()
    db_session.refresh(news)
    return news


class TestGetByTicker:
    def test_get_by_ticker_no_results(self, db_session, repo):
        """Returns ([], 0) when no news exists for the requested ticker."""
        items, total = repo.get_by_ticker(db_session, "UNKNOWN")
        assert items == []
        assert total == 0

    def test_get_by_ticker_returns_results(self, db_session, repo):
        """Inserted news appears in the query result."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 10))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 1, 20))

        items, total = repo.get_by_ticker(db_session, "AAPL")

        assert total == 2
        assert len(items) == 2

    def test_get_by_ticker_start_date_filter(self, db_session, repo):
        """Only news with published_at >= start_date is returned."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))

        items, total = repo.get_by_ticker(
            db_session, "AAPL", start_date=datetime(2024, 2, 1)
        )

        assert total == 2
        returned_ids = {item.finnhub_id for item in items}
        assert returned_ids == {2, 3}

    def test_get_by_ticker_end_date_filter(self, db_session, repo):
        """Only news with published_at <= end_date is returned (inclusive)."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))

        items, total = repo.get_by_ticker(
            db_session, "AAPL", end_date=datetime(2024, 2, 1)
        )

        assert total == 2
        returned_ids = {item.finnhub_id for item in items}
        assert returned_ids == {1, 2}

    def test_get_by_ticker_date_range(self, db_session, repo):
        """Both start and end date filters are applied together."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))
        _insert_news(db_session, finnhub_id=4, published_at=datetime(2024, 4, 1))

        items, total = repo.get_by_ticker(
            db_session,
            "AAPL",
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 3, 1),
        )

        assert total == 2
        returned_ids = {item.finnhub_id for item in items}
        assert returned_ids == {2, 3}

    def test_get_by_ticker_pagination_offset(self, db_session, repo):
        """offset parameter skips the correct number of records."""
        for i in range(1, 6):
            _insert_news(
                db_session,
                finnhub_id=i,
                published_at=datetime(2024, 1, i),
            )

        # Results are ordered published_at DESC: ids 5,4,3,2,1
        items, total = repo.get_by_ticker(db_session, "AAPL", offset=2, limit=10)

        assert total == 5          # total reflects all matching rows
        assert len(items) == 3     # only 3 items remain after skipping 2
        assert items[0].finnhub_id == 3

    def test_get_by_ticker_pagination_limit(self, db_session, repo):
        """limit parameter caps the number of returned records."""
        for i in range(1, 6):
            _insert_news(
                db_session,
                finnhub_id=i,
                published_at=datetime(2024, 1, i),
            )

        items, total = repo.get_by_ticker(db_session, "AAPL", offset=0, limit=2)

        assert total == 5
        assert len(items) == 2

    def test_get_by_ticker_total_count_reflects_all_matching(self, db_session, repo):
        """total is the count of all matching rows, not just the current page."""
        for i in range(1, 11):
            _insert_news(
                db_session,
                finnhub_id=i,
                published_at=datetime(2024, 1, i),
            )

        items, total = repo.get_by_ticker(db_session, "AAPL", offset=0, limit=3)

        assert total == 10
        assert len(items) == 3

    def test_get_by_ticker_boundary_dates_included(self, db_session, repo):
        """News exactly on start_date and end_date boundaries is included."""
        start = datetime(2024, 2, 1, 0, 0, 0)
        end = datetime(2024, 3, 31, 23, 59, 59)

        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 31))  # before
        _insert_news(db_session, finnhub_id=2, published_at=start)                  # on start
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))   # in range
        _insert_news(db_session, finnhub_id=4, published_at=end)                    # on end
        _insert_news(db_session, finnhub_id=5, published_at=datetime(2024, 4, 1))   # after

        items, total = repo.get_by_ticker(
            db_session, "AAPL", start_date=start, end_date=end
        )

        assert total == 3
        returned_ids = {item.finnhub_id for item in items}
        assert returned_ids == {2, 3, 4}

    def test_get_by_ticker_results_ordered_descending(self, db_session, repo):
        """Results are returned in published_at descending order."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 3, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 2, 1))

        items, _ = repo.get_by_ticker(db_session, "AAPL")

        dates = [item.published_at for item in items]
        assert dates == sorted(dates, reverse=True)

    def test_get_by_ticker_isolates_by_ticker_symbol(self, db_session, repo):
        """Only news matching the requested ticker symbol is returned."""
        _insert_news(db_session, ticker_symbol="AAPL", finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, ticker_symbol="MSFT", finnhub_id=2, published_at=datetime(2024, 1, 2))

        items, total = repo.get_by_ticker(db_session, "MSFT")

        assert total == 1
        assert items[0].ticker_symbol == "MSFT"
        assert items[0].finnhub_id == 2
