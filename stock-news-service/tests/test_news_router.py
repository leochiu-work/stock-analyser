"""Integration tests for the news router via FastAPI TestClient.

Data is seeded directly via SQLAlchemy ORM to avoid the PostgreSQL-dialect
upsert. The `client` fixture (defined in conftest.py) wires the test DB
session into the FastAPI app via dependency_overrides.
"""

from datetime import datetime

import pytest

from app.models.news import News


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_news(db_session, **kwargs) -> News:
    """Insert a single News row with sensible defaults."""
    defaults = {
        "ticker_symbol": "AAPL",
        "headline": "Default headline",
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_endpoint(self, client):
        """GET /health returns 200 with status ok."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestGetNewsEndpoint:
    def test_get_news_empty_db(self, client):
        """GET /api/v1/news/AAPL with no data → 200, total=0, items=[]."""
        resp = client.get("/api/v1/news/AAPL")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_get_news_returns_data(self, client, db_session):
        """Inserted news is returned by the endpoint."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 10))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 10))

        resp = client.get("/api/v1/news/AAPL")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_get_news_unknown_ticker(self, client):
        """GET /api/v1/news/UNKNOWN → 200, total=0, items=[]."""
        resp = client.get("/api/v1/news/UNKNOWN")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_get_news_response_schema(self, client):
        """Response body contains total, offset, limit, and items fields."""
        resp = client.get("/api/v1/news/AAPL")
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert "offset" in body
        assert "limit" in body
        assert "items" in body

    def test_get_news_default_pagination_values(self, client):
        """Default offset=0 and limit=50 are reflected in the response."""
        resp = client.get("/api/v1/news/AAPL")
        body = resp.json()
        assert body["offset"] == 0
        assert body["limit"] == 50


class TestGetNewsDateFilters:
    def test_get_news_start_date_filter(self, client, db_session):
        """Only news published on or after start_date is returned."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))

        resp = client.get("/api/v1/news/AAPL?start_date=2024-02-01")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        returned_ids = {item["finnhub_id"] for item in body["items"]}
        assert returned_ids == {2, 3}

    def test_get_news_end_date_filter(self, client, db_session):
        """Only news published on or before end_date is returned."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))

        resp = client.get("/api/v1/news/AAPL?end_date=2024-02-01")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        returned_ids = {item["finnhub_id"] for item in body["items"]}
        assert returned_ids == {1, 2}

    def test_get_news_start_date_after_end_date_returns_400(self, client):
        """start_date > end_date → 400 Bad Request."""
        resp = client.get("/api/v1/news/AAPL?start_date=2024-12-31&end_date=2024-01-01")
        assert resp.status_code == 400
        assert "start_date" in resp.json()["detail"].lower()

    def test_get_news_invalid_date_format_returns_422(self, client):
        """Non-date start_date value → 422 Unprocessable Entity."""
        resp = client.get("/api/v1/news/AAPL?start_date=not-a-date")
        assert resp.status_code == 422

    def test_get_news_date_range_filter(self, client, db_session):
        """Both start_date and end_date are applied together."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))
        _insert_news(db_session, finnhub_id=2, published_at=datetime(2024, 2, 1))
        _insert_news(db_session, finnhub_id=3, published_at=datetime(2024, 3, 1))
        _insert_news(db_session, finnhub_id=4, published_at=datetime(2024, 4, 1))

        resp = client.get("/api/v1/news/AAPL?start_date=2024-02-01&end_date=2024-03-01")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        returned_ids = {item["finnhub_id"] for item in body["items"]}
        assert returned_ids == {2, 3}


class TestGetNewsPagination:
    def test_get_news_pagination_offset(self, client, db_session):
        """offset query param skips the correct number of records."""
        for i in range(1, 6):
            _insert_news(
                db_session,
                finnhub_id=i,
                published_at=datetime(2024, 1, i),
            )

        resp = client.get("/api/v1/news/AAPL?offset=2&limit=10")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 3
        assert body["offset"] == 2

    def test_get_news_pagination_limit(self, client, db_session):
        """limit query param caps the number of returned items."""
        for i in range(1, 6):
            _insert_news(
                db_session,
                finnhub_id=i,
                published_at=datetime(2024, 1, i),
            )

        resp = client.get("/api/v1/news/AAPL?limit=2")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["limit"] == 2

    def test_get_news_offset_beyond_total_returns_empty_items(self, client, db_session):
        """An offset larger than the total count returns [] for items."""
        _insert_news(db_session, finnhub_id=1, published_at=datetime(2024, 1, 1))

        resp = client.get("/api/v1/news/AAPL?offset=100")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"] == []

    def test_get_news_negative_offset_returns_422(self, client):
        """offset < 0 → 422 Unprocessable Entity."""
        resp = client.get("/api/v1/news/AAPL?offset=-1")
        assert resp.status_code == 422

    def test_get_news_zero_limit_returns_422(self, client):
        """limit=0 → 422 Unprocessable Entity."""
        resp = client.get("/api/v1/news/AAPL?limit=0")
        assert resp.status_code == 422

    def test_get_news_limit_above_500_returns_422(self, client):
        """limit > 500 → 422 Unprocessable Entity."""
        resp = client.get("/api/v1/news/AAPL?limit=501")
        assert resp.status_code == 422

    def test_get_news_max_limit_500_accepted(self, client):
        """limit=500 is the allowed maximum and should return 200."""
        resp = client.get("/api/v1/news/AAPL?limit=500")
        assert resp.status_code == 200


class TestGetNewsItemShape:
    def test_get_news_item_fields(self, client, db_session):
        """Each item in the response contains the expected fields."""
        _insert_news(
            db_session,
            finnhub_id=42,
            ticker_symbol="AAPL",
            headline="Test headline",
            summary="Test summary",
            source="Reuters",
            url="http://example.com/42",
            image="http://example.com/img/42.jpg",
            category="company news",
            published_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        resp = client.get("/api/v1/news/AAPL")
        item = resp.json()["items"][0]

        assert item["finnhub_id"] == 42
        assert item["ticker_symbol"] == "AAPL"
        assert item["headline"] == "Test headline"
        assert item["summary"] == "Test summary"
        assert item["source"] == "Reuters"
        assert item["url"] == "http://example.com/42"
        assert item["image"] == "http://example.com/img/42.jpg"
        assert item["category"] == "company news"
        assert "published_at" in item

    def test_get_news_ticker_lookup_is_case_insensitive_via_service(self, client, db_session):
        """The service uppercases the ticker before querying; lowercase path works."""
        _insert_news(db_session, ticker_symbol="AAPL", finnhub_id=1, published_at=datetime(2024, 1, 1))

        resp = client.get("/api/v1/news/aapl")

        assert resp.status_code == 200
        # NewsService uppercases the ticker before passing to the repository
        assert resp.json()["total"] == 1
