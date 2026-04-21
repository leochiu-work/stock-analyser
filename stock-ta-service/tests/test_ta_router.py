"""Tests for TA router — mocks ta_repository."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.ta_indicator import TAIndicator


def _make_ta_row(ticker="AAPL", row_date=date(2024, 1, 2)):
    row = MagicMock(spec=TAIndicator)
    row.ticker = ticker
    row.date = row_date
    row.sma_20 = 150.0
    row.sma_50 = 148.0
    row.sma_200 = None
    row.ema_12 = 151.0
    row.ema_26 = 149.0
    row.rsi_14 = 55.0
    row.macd_line = 2.0
    row.macd_signal = 1.5
    row.macd_hist = 0.5
    row.bb_upper = 160.0
    row.bb_middle = 150.0
    row.bb_lower = 140.0
    row.atr_14 = 3.5
    row.stoch_k = 70.0
    row.stoch_d = 65.0
    return row


def test_get_ta_returns_list(test_client: TestClient):
    with patch("app.routers.ta_router.TARepository") as MockRepo:
        MockRepo.return_value.get_by_ticker.return_value = [_make_ta_row()]
        resp = test_client.get("/api/v1/ta/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert len(data["items"]) == 1
    assert data["items"][0]["sma_20"] == 150.0


def test_get_ta_empty_list(test_client: TestClient):
    with patch("app.routers.ta_router.TARepository") as MockRepo:
        MockRepo.return_value.get_by_ticker.return_value = []
        resp = test_client.get("/api/v1/ta/NVDA")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_get_ta_invalid_date_range(test_client: TestClient):
    resp = test_client.get("/api/v1/ta/AAPL?start_date=2024-12-31&end_date=2024-01-01")
    assert resp.status_code == 400


def test_get_latest_ta(test_client: TestClient):
    with patch("app.routers.ta_router.TARepository") as MockRepo:
        MockRepo.return_value.get_latest.return_value = _make_ta_row()
        resp = test_client.get("/api/v1/ta/AAPL/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["rsi_14"] == 55.0


def test_get_latest_ta_not_found(test_client: TestClient):
    with patch("app.routers.ta_router.TARepository") as MockRepo:
        MockRepo.return_value.get_latest.return_value = None
        resp = test_client.get("/api/v1/ta/NVDA/latest")
    assert resp.status_code == 404


def test_health_check(test_client: TestClient):
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
