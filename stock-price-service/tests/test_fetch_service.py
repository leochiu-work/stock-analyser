"""Unit tests for FetchService (yfinance is mocked)."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.fetch_service import FetchService


def _make_flat_df(rows: list[dict]) -> pd.DataFrame:
    """Build a flat-column DataFrame as returned by yfinance for a single ticker."""
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("Date"))
    df.index.name = "Date"
    return df


def _make_multiindex_df(rows: list[dict], ticker: str) -> pd.DataFrame:
    """Build a MultiIndex-column DataFrame as yfinance returns in some versions."""
    flat = _make_flat_df(rows)
    flat.columns = pd.MultiIndex.from_tuples(
        [(col, ticker) for col in flat.columns], names=["Price", "Ticker"]
    )
    return flat


# ---------------------------------------------------------------------------

class TestFetchPrices:
    def test_returns_empty_list_when_df_is_empty(self):
        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = pd.DataFrame()
            result = FetchService().fetch_prices("AAPL", date(2024, 1, 1), date(2024, 1, 5))
        assert result == []

    def test_parses_flat_columns(self):
        rows = [{"Date": "2024-01-02", "Open": 100.0, "High": 110.0, "Low": 90.0, "Close": 105.0}]
        df = _make_flat_df(rows)

        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = df
            result = FetchService().fetch_prices("AAPL", date(2024, 1, 2), date(2024, 1, 2))

        assert len(result) == 1
        r = result[0]
        assert r["ticker"] == "AAPL"
        assert r["date"] == date(2024, 1, 2)
        assert r["open"] == 100.0
        assert r["high"] == 110.0
        assert r["low"] == 90.0
        assert r["close"] == 105.0

    def test_parses_multiindex_columns(self):
        rows = [{"Date": "2024-01-02", "Open": 150.0, "High": 155.0, "Low": 148.0, "Close": 153.0}]
        df = _make_multiindex_df(rows, "TSLA")

        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = df
            result = FetchService().fetch_prices("TSLA", date(2024, 1, 2), date(2024, 1, 2))

        assert len(result) == 1
        assert result[0]["ticker"] == "TSLA"
        assert result[0]["close"] == 153.0

    def test_ticker_is_uppercased(self):
        rows = [{"Date": "2024-01-02", "Open": 100.0, "High": 110.0, "Low": 90.0, "Close": 105.0}]
        df = _make_flat_df(rows)

        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = df
            result = FetchService().fetch_prices("aapl", date(2024, 1, 2), date(2024, 1, 2))

        assert result[0]["ticker"] == "AAPL"

    def test_multiple_rows_returned(self):
        rows = [
            {"Date": "2024-01-02", "Open": 100.0, "High": 110.0, "Low": 90.0, "Close": 105.0},
            {"Date": "2024-01-03", "Open": 105.0, "High": 115.0, "Low": 100.0, "Close": 112.0},
            {"Date": "2024-01-04", "Open": 112.0, "High": 120.0, "Low": 108.0, "Close": 118.0},
        ]
        df = _make_flat_df(rows)

        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = df
            result = FetchService().fetch_prices("AAPL", date(2024, 1, 2), date(2024, 1, 4))

        assert len(result) == 3
        assert result[0]["date"] == date(2024, 1, 2)
        assert result[2]["date"] == date(2024, 1, 4)

    def test_end_date_passed_as_exclusive_to_yfinance(self):
        """yfinance end is exclusive; the service adds 1 day so end_date is included."""
        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = pd.DataFrame()
            FetchService().fetch_prices("AAPL", date(2024, 1, 1), date(2024, 1, 31))

        _, kwargs = mock_dl.call_args
        assert kwargs["end"] == "2024-02-01"

    def test_float_conversion(self):
        """Ensure values come back as Python floats, not numpy types."""
        import numpy as np
        rows = [{"Date": "2024-01-02", "Open": np.float64(100.5), "High": np.float64(110.5),
                 "Low": np.float64(90.5), "Close": np.float64(105.5)}]
        df = _make_flat_df(rows)

        with patch("app.services.fetch_service.yf.download") as mock_dl:
            mock_dl.return_value = df
            result = FetchService().fetch_prices("AAPL", date(2024, 1, 2), date(2024, 1, 2))

        assert isinstance(result[0]["open"], float)
        assert isinstance(result[0]["close"], float)
