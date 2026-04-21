"""Unit tests for ta_calculator — pure pandas-ta logic."""
from datetime import date, timedelta

import pytest

from app.services.ta_calculator import compute
from tests.conftest import make_ohlc_records


def test_compute_returns_correct_count():
    records = make_ohlc_records(n=300)
    result = compute("AAPL", records)
    assert len(result) == 300


def test_compute_has_required_columns():
    records = make_ohlc_records(n=300)
    result = compute("AAPL", records)
    row = result[-1]  # last row should have most indicators
    expected_keys = [
        "ticker", "date",
        "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26",
        "rsi_14",
        "macd_line", "macd_signal", "macd_hist",
        "bb_upper", "bb_middle", "bb_lower",
        "atr_14",
        "stoch_k", "stoch_d",
    ]
    for key in expected_keys:
        assert key in row, f"Missing key: {key}"


def test_compute_ticker_is_uppercase():
    records = make_ohlc_records(n=300)
    result = compute("aapl", records)
    assert all(r["ticker"] == "AAPL" for r in result)


def test_compute_early_rows_have_none_for_sma200():
    records = make_ohlc_records(n=300)
    result = compute("AAPL", records)
    # First 199 rows cannot have SMA-200
    for row in result[:199]:
        assert row["sma_200"] is None


def test_compute_later_rows_have_sma20():
    records = make_ohlc_records(n=300)
    result = compute("AAPL", records)
    # Rows after index 19 should have SMA-20
    for row in result[20:]:
        assert row["sma_20"] is not None


def test_compute_returns_empty_for_no_records():
    result = compute("AAPL", [])
    assert result == []


def test_compute_date_is_date_object():
    records = make_ohlc_records(n=30)
    result = compute("AAPL", records)
    from datetime import date
    for row in result:
        assert isinstance(row["date"], date)
