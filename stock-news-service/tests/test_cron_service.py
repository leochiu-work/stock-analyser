"""Unit tests for CronService.run() — all collaborators are mocked."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.cron_service import CronService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ticker(symbol: str, last_fetch_date: date | None = None) -> MagicMock:
    """Build a mock Ticker ORM object."""
    t = MagicMock()
    t.symbol = symbol
    t.last_fetch_date = last_fetch_date
    return t


def _make_service(
    tickers: list,
    fetch_side_effect=None,
    upsert_return: int = 0,
) -> tuple[CronService, MagicMock, MagicMock, MagicMock]:
    """
    Build a CronService with all collaborators replaced by mocks.

    Returns (service, fetch_service_mock, ticker_repo_mock, news_repo_mock).

    CronService.run() calls:
        self.fetch_service.fetch_news(symbol, from_date, to_date)
        self.news_repo.upsert_many(self.db, records)
        self.ticker_repo.update_last_fetch_date(self.db, symbol, today)
    """
    db = MagicMock()
    fetch_service = MagicMock()
    ticker_repo = MagicMock()
    news_repo = MagicMock()

    ticker_repo.get_all.return_value = tickers
    news_repo.upsert_many.return_value = upsert_return

    if fetch_side_effect is not None:
        fetch_service.fetch_news.side_effect = fetch_side_effect
    else:
        fetch_service.fetch_news.return_value = []

    service = CronService(
        db=db,
        fetch_service=fetch_service,
        ticker_repo=ticker_repo,
        news_repo=news_repo,
    )
    return service, fetch_service, ticker_repo, news_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCronServiceRun:
    def test_run_empty_tickers(self):
        """No tickers in DB → returns {}, fetch never called."""
        service, fetch_service, _, _ = _make_service([])

        result = service.run()

        assert result == {}
        fetch_service.fetch_news.assert_not_called()

    def test_run_single_ticker_success(self):
        """Single ticker with 2 fetched items → result has status=ok and count=2."""
        ticker = _make_ticker("AAPL", last_fetch_date=date(2024, 1, 1))
        records = [{"finnhub_id": 1}, {"finnhub_id": 2}]
        service, _, ticker_repo, news_repo = _make_service(
            [ticker],
            fetch_side_effect=lambda sym, from_d, to_d: records,
            upsert_return=2,
        )

        result = service.run()

        assert result == {"AAPL": {"status": "ok", "count": 2}}
        news_repo.upsert_many.assert_called_once()
        ticker_repo.update_last_fetch_date.assert_called_once()

    def test_run_uses_last_fetch_date_as_from_date(self):
        """When last_fetch_date is set, it is passed as from_date to fetch_news."""
        last = date(2024, 1, 1)
        ticker = _make_ticker("AAPL", last_fetch_date=last)
        service, fetch_service, _, _ = _make_service([ticker])

        service.run()

        # fetch_news(symbol, from_date, to_date)
        _, from_date_passed, _ = fetch_service.fetch_news.call_args[0]
        assert from_date_passed == last

    def test_run_uses_default_30_days_when_no_fetch_date(self):
        """When last_fetch_date is None, from_date is today - 30 days."""
        ticker = _make_ticker("AAPL", last_fetch_date=None)
        service, fetch_service, _, _ = _make_service([ticker])

        with patch("app.services.cron_service.date") as mock_date:
            today = date(2024, 6, 1)
            # Make date.today() return our fixed date; keep date() constructor working
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            service.run()

        _, from_date_passed, _ = fetch_service.fetch_news.call_args[0]
        assert from_date_passed == today - timedelta(days=30)

    def test_run_empty_fetch_result(self):
        """fetch_news returning [] → upsert called with [], count=0, date still updated."""
        ticker = _make_ticker("AAPL", last_fetch_date=date(2024, 5, 1))
        service, _, ticker_repo, news_repo = _make_service(
            [ticker],
            fetch_side_effect=lambda sym, from_d, to_d: [],
            upsert_return=0,
        )

        result = service.run()

        assert result["AAPL"] == {"status": "ok", "count": 0}
        # upsert_many(db, [])
        _db_arg, records_arg = news_repo.upsert_many.call_args[0]
        assert records_arg == []
        ticker_repo.update_last_fetch_date.assert_called_once()

    def test_run_multiple_tickers(self):
        """Two tickers → fetch called twice, both appear in result."""
        tickers = [
            _make_ticker("AAPL", last_fetch_date=date(2024, 1, 1)),
            _make_ticker("MSFT", last_fetch_date=date(2024, 1, 1)),
        ]
        service, fetch_service, ticker_repo, _ = _make_service(tickers)

        result = service.run()

        assert set(result.keys()) == {"AAPL", "MSFT"}
        assert fetch_service.fetch_news.call_count == 2
        assert ticker_repo.update_last_fetch_date.call_count == 2

    def test_run_fetch_exception_produces_error_status(self):
        """fetch_news raising an exception → status='error', date not updated."""
        ticker = _make_ticker("FAIL", last_fetch_date=date(2024, 1, 1))
        service, _, ticker_repo, _ = _make_service(
            [ticker],
            fetch_side_effect=RuntimeError("network error"),
        )

        result = service.run()

        assert result["FAIL"] == {"status": "error"}
        ticker_repo.update_last_fetch_date.assert_not_called()

    def test_run_continues_after_one_ticker_fails(self):
        """An error on one ticker does not prevent other tickers from being processed."""
        def _side_effect(sym, from_d, to_d):
            if sym == "FAIL":
                raise RuntimeError("bad ticker")
            return []

        tickers = [
            _make_ticker("FAIL", last_fetch_date=date(2024, 1, 1)),
            _make_ticker("MSFT", last_fetch_date=date(2024, 1, 1)),
        ]
        service, _, _, _ = _make_service(tickers, fetch_side_effect=_side_effect)

        result = service.run()

        assert result["FAIL"]["status"] == "error"
        assert result["MSFT"]["status"] == "ok"

    def test_run_upsert_called_with_correct_records(self):
        """The exact records from fetch_news are forwarded to news_repo.upsert_many."""
        records = [{"finnhub_id": 10, "headline": "Breaking news"}]
        ticker = _make_ticker("AAPL", last_fetch_date=date(2024, 1, 1))
        service, _, _, news_repo = _make_service(
            [ticker],
            fetch_side_effect=lambda sym, from_d, to_d: records,
            upsert_return=1,
        )

        service.run()

        # upsert_many is called as upsert_many(db, records)
        _db_arg, records_arg = news_repo.upsert_many.call_args[0]
        assert records_arg == records

    def test_run_last_fetch_date_updated_to_today(self):
        """update_last_fetch_date is called with today's date on success."""
        ticker = _make_ticker("AAPL", last_fetch_date=date(2024, 1, 1))
        service, _, ticker_repo, _ = _make_service([ticker])

        with patch("app.services.cron_service.date") as mock_date:
            today = date(2024, 7, 15)
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            service.run()

        # update_last_fetch_date(db, symbol, today)
        _db_arg, symbol_arg, date_arg = ticker_repo.update_last_fetch_date.call_args[0]
        assert symbol_arg == "AAPL"
        assert date_arg == today

    def test_run_to_date_is_today(self):
        """to_date passed to fetch_news is today's date."""
        ticker = _make_ticker("AAPL", last_fetch_date=date(2024, 1, 1))
        service, fetch_service, _, _ = _make_service([ticker])

        with patch("app.services.cron_service.date") as mock_date:
            today = date(2024, 8, 1)
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            service.run()

        _, _, to_date_passed = fetch_service.fetch_news.call_args[0]
        assert to_date_passed == today
