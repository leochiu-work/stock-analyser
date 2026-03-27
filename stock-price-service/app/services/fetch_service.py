from datetime import date, timedelta

import pandas as pd
import yfinance as yf


class FetchService:
    def fetch_prices(self, ticker: str, start_date: date, end_date: date) -> list[dict]:
        """
        Fetch OHLC prices for a single ticker from yfinance.
        Returns a list of dicts ready for DB insertion.
        """
        # yfinance end date is exclusive, so add 1 day to include end_date
        df: pd.DataFrame = yf.download(
            ticker,
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
        )

        if df.empty:
            return []

        # Normalize MultiIndex columns (yfinance >= 0.2 wraps single tickers too)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, axis=1, level="Ticker")

        records = []
        for idx, row in df.iterrows():
            records.append(
                {
                    "ticker": ticker.upper(),
                    "date": idx.date() if hasattr(idx, "date") else idx,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                }
            )
        return records
