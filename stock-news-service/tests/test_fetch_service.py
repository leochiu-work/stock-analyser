"""Unit tests for FetchService (finnhub.Client is mocked)."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.fetch_service import FetchService


def _make_finnhub_item(
    id: int = 42,
    headline: str = "Test headline",
    summary: str = "Test summary",
    source: str = "Reuters",
    url: str = "http://example.com/news/42",
    image: str = "http://example.com/img/42.jpg",
    category: str = "company news",
    datetime_ts: int = 1705312800,  # 2024-01-15 10:00:00 UTC
) -> dict:
    """Build a minimal Finnhub news item dict."""
    return {
        "id": id,
        "headline": headline,
        "summary": summary,
        "source": source,
        "url": url,
        "image": image,
        "category": category,
        "datetime": datetime_ts,
    }


class TestFetchNewsMapping:
    def test_fetch_news_returns_mapped_records(self):
        """A valid Finnhub response is mapped to the expected record structure."""
        ts = 1705312800  # 2024-01-15 10:00:00 UTC
        item = _make_finnhub_item(id=99, headline="Big news", datetime_ts=ts)

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = [item]
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        assert len(records) == 1
        r = records[0]
        assert r["finnhub_id"] == 99
        assert r["headline"] == "Big news"
        assert r["ticker_symbol"] == "AAPL"
        assert r["source"] == "Reuters"
        assert r["url"] == "http://example.com/news/42"
        assert r["image"] == "http://example.com/img/42.jpg"
        assert r["category"] == "company news"

    def test_fetch_news_ticker_uppercased(self):
        """ticker_symbol in the returned record is always uppercased."""
        item = _make_finnhub_item(id=1)

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = [item]
            service = FetchService(api_key="test-key")

        records = service.fetch_news("aapl", date(2024, 1, 1), date(2024, 1, 31))

        assert records[0]["ticker_symbol"] == "AAPL"

    def test_fetch_news_empty_result(self):
        """An empty list from Finnhub produces an empty result."""
        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = []
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        assert records == []

    def test_fetch_news_none_result(self):
        """None from Finnhub is treated as empty (graceful handling)."""
        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = None
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        assert records == []

    def test_fetch_news_datetime_conversion(self):
        """Unix timestamp is correctly converted to a naive UTC datetime."""
        # 2024-01-15 10:00:00 UTC  →  unix 1705312800
        ts = 1705312800
        expected_dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = [_make_finnhub_item(id=1, datetime_ts=ts)]
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        assert records[0]["published_at"] == expected_dt
        # Must be timezone-naive
        assert records[0]["published_at"].tzinfo is None

    def test_fetch_news_multiple_items_all_mapped(self):
        """All items in the Finnhub response are mapped and returned."""
        items = [_make_finnhub_item(id=i, headline=f"Headline {i}") for i in range(1, 4)]

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = items
            service = FetchService(api_key="test-key")

        records = service.fetch_news("MSFT", date(2024, 1, 1), date(2024, 1, 31))

        assert len(records) == 3
        assert {r["finnhub_id"] for r in records} == {1, 2, 3}

    def test_fetch_news_falsy_optional_fields_become_none(self):
        """Items with empty-string optional fields produce None in the record."""
        item = {
            "id": 7,
            "headline": "Sparse item",
            "summary": "",
            "source": "",
            "url": "",
            "image": "",
            "category": "",
            "datetime": 1705312800,
        }

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = [item]
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        r = records[0]
        assert r["summary"] is None
        assert r["source"] is None
        assert r["url"] is None
        assert r["image"] is None
        assert r["category"] is None

    def test_fetch_news_missing_optional_keys_become_none(self):
        """Items missing optional keys entirely produce None values in the record."""
        item = {
            "id": 8,
            "headline": "Minimal item",
            "datetime": 1705312800,
        }

        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = [item]
            service = FetchService(api_key="test-key")

        records = service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        r = records[0]
        assert r["summary"] is None
        assert r["source"] is None
        assert r["url"] is None
        assert r["image"] is None
        assert r["category"] is None

    def test_fetch_news_passes_correct_date_range_to_client(self):
        """The correct ISO date strings are passed to the Finnhub client."""
        with patch("app.services.fetch_service.finnhub") as mock_finnhub:
            mock_client = MagicMock()
            mock_finnhub.Client.return_value = mock_client
            mock_client.company_news.return_value = []
            service = FetchService(api_key="test-key")

        service.fetch_news("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        service.client.company_news.assert_called_once_with(
            "AAPL",
            _from="2024-01-01",
            to="2024-01-31",
        )
