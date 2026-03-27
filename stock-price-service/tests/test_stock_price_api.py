"""Unit tests for GET /api/v1/stocks/{ticker} endpoint."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.stock_price import StockPriceItem, StockPriceListResponse
from tests.conftest import make_stock_price_orm


def _empty_response(ticker: str = "AAPL", offset: int = 0, limit: int = 50) -> StockPriceListResponse:
    return StockPriceListResponse(ticker=ticker, total=0, offset=offset, limit=limit, items=[])


def _item(ticker: str = "AAPL", price_date: date = date(2024, 1, 2)) -> StockPriceItem:
    return StockPriceItem(ticker=ticker, date=price_date, open=100, high=110, low=90, close=105)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_service(test_client: TestClient, return_value: StockPriceListResponse):
    """Patch StockPriceService.get_prices for the duration of a test."""
    return patch(
        "app.routers.stock_prices.StockPriceService",
        return_value=MagicMock(get_prices=MagicMock(return_value=return_value)),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetTickerPrices:
    def test_returns_200_with_empty_items(self, test_client: TestClient):
        with _patch_service(test_client, _empty_response()):
            resp = test_client.get("/api/v1/stocks/AAPL")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ticker"] == "AAPL"
        assert body["total"] == 0
        assert body["items"] == []

    def test_returns_items(self, test_client: TestClient):
        response = StockPriceListResponse(
            ticker="AAPL",
            total=1,
            offset=0,
            limit=50,
            items=[_item()],
        )
        with _patch_service(test_client, response):
            resp = test_client.get("/api/v1/stocks/AAPL")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["ticker"] == "AAPL"
        assert items[0]["close"] == 105.0

    def test_ticker_is_uppercased_before_service_call(self, test_client: TestClient):
        mock_svc = MagicMock(get_prices=MagicMock(return_value=_empty_response("AAPL")))
        with patch("app.routers.stock_prices.StockPriceService", return_value=mock_svc):
            test_client.get("/api/v1/stocks/aapl")
        mock_svc.get_prices.assert_called_once()
        assert mock_svc.get_prices.call_args[0][0] == "aapl"  # router passes raw; service uppercases

    def test_start_date_and_end_date_forwarded(self, test_client: TestClient):
        mock_svc = MagicMock(get_prices=MagicMock(return_value=_empty_response()))
        with patch("app.routers.stock_prices.StockPriceService", return_value=mock_svc):
            test_client.get("/api/v1/stocks/AAPL?start_date=2024-01-01&end_date=2024-06-30")
        args, _ = mock_svc.get_prices.call_args
        # get_prices(ticker, start_date, end_date, offset, limit)
        assert args[1] == date(2024, 1, 1)
        assert args[2] == date(2024, 6, 30)

    def test_start_date_after_end_date_returns_400(self, test_client: TestClient):
        resp = test_client.get("/api/v1/stocks/AAPL?start_date=2024-12-31&end_date=2024-01-01")
        assert resp.status_code == 400
        assert "start_date" in resp.json()["detail"].lower()

    def test_invalid_date_format_returns_422(self, test_client: TestClient):
        resp = test_client.get("/api/v1/stocks/AAPL?start_date=not-a-date")
        assert resp.status_code == 422

    def test_negative_offset_returns_422(self, test_client: TestClient):
        resp = test_client.get("/api/v1/stocks/AAPL?offset=-1")
        assert resp.status_code == 422

    def test_zero_limit_returns_422(self, test_client: TestClient):
        resp = test_client.get("/api/v1/stocks/AAPL?limit=0")
        assert resp.status_code == 422

    def test_limit_above_500_returns_422(self, test_client: TestClient):
        resp = test_client.get("/api/v1/stocks/AAPL?limit=501")
        assert resp.status_code == 422

    def test_pagination_params_forwarded(self, test_client: TestClient):
        mock_svc = MagicMock(get_prices=MagicMock(return_value=_empty_response(offset=20, limit=10)))
        with patch("app.routers.stock_prices.StockPriceService", return_value=mock_svc):
            resp = test_client.get("/api/v1/stocks/AAPL?offset=20&limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert body["offset"] == 20
        assert body["limit"] == 10

    def test_health_endpoint(self, test_client: TestClient):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_default_pagination_values(self, test_client: TestClient):
        mock_svc = MagicMock(get_prices=MagicMock(return_value=_empty_response()))
        with patch("app.routers.stock_prices.StockPriceService", return_value=mock_svc):
            test_client.get("/api/v1/stocks/AAPL")
        args, _ = mock_svc.get_prices.call_args
        # get_prices(ticker, start_date, end_date, offset, limit)
        assert args[3] == 0    # offset
        assert args[4] == 50   # limit

    def test_max_limit_500_accepted(self, test_client: TestClient):
        mock_svc = MagicMock(get_prices=MagicMock(return_value=_empty_response()))
        with patch("app.routers.stock_prices.StockPriceService", return_value=mock_svc):
            resp = test_client.get("/api/v1/stocks/AAPL?limit=500")
        assert resp.status_code == 200
