"""Tests for ta_service — mocks price_client and ta_repository."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.ta_service import compute_and_store
from tests.conftest import make_ohlc_records


def test_compute_and_store_calls_fetch_and_upsert():
    mock_db = MagicMock()
    ohlc = make_ohlc_records(n=50)

    with (
        patch("app.services.ta_service.TickerRepository") as MockTickerRepo,
        patch("app.services.ta_service.price_client") as mock_pc,
        patch("app.services.ta_service.ta_calculator") as mock_calc,
        patch("app.services.ta_service.TARepository") as MockTARepo,
    ):
        mock_pc.fetch_ohlc.return_value = ohlc
        mock_calc.compute.return_value = [{"ticker": "AAPL", "date": date(2024, 1, 2)}]
        MockTARepo.return_value.upsert_many.return_value = 1

        result = compute_and_store(mock_db, "AAPL")

    assert result == 1
    mock_pc.fetch_ohlc.assert_called_once_with("AAPL")
    mock_calc.compute.assert_called_once()
    MockTARepo.return_value.upsert_many.assert_called_once()


def test_compute_and_store_returns_zero_when_no_ohlc():
    mock_db = MagicMock()

    with (
        patch("app.services.ta_service.TickerRepository"),
        patch("app.services.ta_service.price_client") as mock_pc,
        patch("app.services.ta_service.ta_calculator") as mock_calc,
        patch("app.services.ta_service.TARepository"),
    ):
        mock_pc.fetch_ohlc.return_value = []
        result = compute_and_store(mock_db, "AAPL")

    assert result == 0
    mock_calc.compute.assert_not_called()


def test_compute_and_store_creates_ticker():
    mock_db = MagicMock()
    ohlc = make_ohlc_records(n=30)

    with (
        patch("app.services.ta_service.TickerRepository") as MockTickerRepo,
        patch("app.services.ta_service.price_client") as mock_pc,
        patch("app.services.ta_service.ta_calculator") as mock_calc,
        patch("app.services.ta_service.TARepository") as MockTARepo,
    ):
        mock_pc.fetch_ohlc.return_value = ohlc
        mock_calc.compute.return_value = []
        MockTARepo.return_value.upsert_many.return_value = 0

        compute_and_store(mock_db, "MSFT")

    MockTickerRepo.return_value.get_or_create.assert_called_once_with("MSFT")
