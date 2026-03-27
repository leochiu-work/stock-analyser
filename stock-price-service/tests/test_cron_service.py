"""Unit tests for CronService (repositories and FetchService are mocked)."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.cron_service import CronService
from tests.conftest import make_ticker_orm


def _make_service(
    tickers: list,
    fetch_records: dict[str, list] | None = None,
    upsert_rowcount: int = 3,
) -> tuple[CronService, MagicMock, MagicMock, MagicMock]:
    """
    Build a CronService with mocked internals.
    Returns (service, stock_repo, ticker_repo, fetch_service).
    """
    db = MagicMock()
    fetch_service = MagicMock()
    fetch_records = fetch_records or {}

    with (
        patch("app.services.cron_service.StockPriceRepository") as MockStockRepo,
        patch("app.services.cron_service.TickerRepository") as MockTickerRepo,
    ):
        stock_repo = MagicMock()
        ticker_repo = MagicMock()
        MockStockRepo.return_value = stock_repo
        MockTickerRepo.return_value = ticker_repo

        ticker_repo.get_all.return_value = tickers
        stock_repo.upsert_many.return_value = upsert_rowcount

        def _fetch(symbol, start, end):
            return fetch_records.get(symbol, [])

        fetch_service.fetch_prices.side_effect = _fetch

        service = CronService(db, fetch_service=fetch_service)
        service.stock_repo = stock_repo
        service.ticker_repo = ticker_repo

    return service, stock_repo, ticker_repo, fetch_service


class TestCronServiceRun:
    def test_no_tickers_returns_empty(self):
        service, _, _, _ = _make_service([])
        result = service.run()
        assert result == {}

    def test_skips_ticker_already_fetched_today(self):
        today = date.today()
        ticker = make_ticker_orm("AAPL", last_fetch_date=today)
        service, stock_repo, ticker_repo, fetch_service = _make_service([ticker])

        result = service.run()

        assert result["AAPL"]["status"] == "skipped"
        fetch_service.fetch_prices.assert_not_called()
        stock_repo.upsert_many.assert_not_called()

    def test_skips_ticker_fetched_in_future(self):
        future = date.today() + timedelta(days=1)
        ticker = make_ticker_orm("AAPL", last_fetch_date=future)
        service, _, _, fetch_service = _make_service([ticker])

        result = service.run()

        assert result["AAPL"]["status"] == "skipped"
        fetch_service.fetch_prices.assert_not_called()

    def test_fetches_from_default_start_date_when_last_fetch_is_none(self):
        ticker = make_ticker_orm("AAPL", last_fetch_date=None)
        service, stock_repo, ticker_repo, fetch_service = _make_service(
            [ticker], fetch_records={"AAPL": [{"ticker": "AAPL"}] * 5}, upsert_rowcount=5
        )

        with patch("app.services.cron_service.settings") as mock_settings:
            mock_settings.default_start_date = date(2020, 1, 1)
            result = service.run()

        call_args = fetch_service.fetch_prices.call_args
        assert call_args[0][1] == date(2020, 1, 1)
        assert result["AAPL"]["status"] == "ok"
        assert result["AAPL"]["records_upserted"] == 5

    def test_fetches_from_last_fetch_date_plus_one(self):
        last = date(2024, 6, 1)
        ticker = make_ticker_orm("AAPL", last_fetch_date=last)
        service, _, _, fetch_service = _make_service([ticker])

        service.run()

        call_args = fetch_service.fetch_prices.call_args
        assert call_args[0][1] == last + timedelta(days=1)

    def test_updates_last_fetch_date_on_success(self):
        today = date.today()
        last = today - timedelta(days=5)
        ticker = make_ticker_orm("AAPL", last_fetch_date=last)
        service, _, ticker_repo, _ = _make_service([ticker])

        service.run()

        ticker_repo.update_last_fetch_date.assert_called_once_with("AAPL", today)

    def test_does_not_update_last_fetch_date_on_error(self):
        last = date.today() - timedelta(days=1)
        ticker = make_ticker_orm("AAPL", last_fetch_date=last)
        service, _, ticker_repo, fetch_service = _make_service([ticker])
        fetch_service.fetch_prices.side_effect = RuntimeError("network error")

        result = service.run()

        assert result["AAPL"]["status"] == "error"
        ticker_repo.update_last_fetch_date.assert_not_called()

    def test_processes_multiple_tickers(self):
        today = date.today()
        last = today - timedelta(days=3)
        tickers = [
            make_ticker_orm("AAPL", last_fetch_date=last),
            make_ticker_orm("MSFT", last_fetch_date=last),
            make_ticker_orm("TSLA", last_fetch_date=last),
        ]
        service, stock_repo, ticker_repo, fetch_service = _make_service(tickers, upsert_rowcount=2)

        result = service.run()

        assert len(result) == 3
        assert all(r["status"] == "ok" for r in result.values())
        assert fetch_service.fetch_prices.call_count == 3
        assert ticker_repo.update_last_fetch_date.call_count == 3

    def test_continues_processing_after_one_ticker_fails(self):
        today = date.today()
        last = today - timedelta(days=1)
        tickers = [
            make_ticker_orm("FAIL", last_fetch_date=last),
            make_ticker_orm("MSFT", last_fetch_date=last),
        ]
        service, stock_repo, ticker_repo, fetch_service = _make_service(tickers)

        def _side_effect(symbol, *args, **kwargs):
            if symbol == "FAIL":
                raise RuntimeError("bad ticker")
            return []

        fetch_service.fetch_prices.side_effect = _side_effect

        result = service.run()

        assert result["FAIL"]["status"] == "error"
        assert result["MSFT"]["status"] == "ok"

    def test_upsert_called_with_fetched_records(self):
        last = date.today() - timedelta(days=1)
        ticker = make_ticker_orm("AAPL", last_fetch_date=last)
        records = [{"ticker": "AAPL", "date": date.today(), "open": 1, "high": 2, "low": 1, "close": 2}]
        service, stock_repo, _, fetch_service = _make_service(
            [ticker], fetch_records={"AAPL": records}
        )

        service.run()

        stock_repo.upsert_many.assert_called_once_with(records)

    def test_zero_records_still_updates_last_fetch_date(self):
        """Market was closed — yfinance returned nothing, but last_fetch_date should update."""
        last = date.today() - timedelta(days=1)
        ticker = make_ticker_orm("AAPL", last_fetch_date=last)
        service, stock_repo, ticker_repo, _ = _make_service(
            [ticker], fetch_records={"AAPL": []}, upsert_rowcount=0
        )

        result = service.run()

        assert result["AAPL"]["status"] == "ok"
        assert result["AAPL"]["records_upserted"] == 0
        ticker_repo.update_last_fetch_date.assert_called_once_with("AAPL", date.today())
