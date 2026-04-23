from __future__ import annotations

import logging
from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from app.agents.state import StrategyState
from app.config import settings
from app.services import price_client, ta_client

logger = logging.getLogger(__name__)

_DROP_COLUMNS = {"ticker", "id", "created_at", "updated_at"}


def run(state: StrategyState) -> dict:
    end_date = date.today()
    start_date = end_date - relativedelta(years=settings.backtest_years)

    ticker = state["ticker"]
    iteration = state["iteration"]

    prices = price_client.get_prices(ticker, start_date, end_date)
    indicators = ta_client.get_indicators(ticker, start_date, end_date)

    df_prices = pd.DataFrame(prices)
    df_indicators = pd.DataFrame(indicators)

    merged = pd.merge(df_prices, df_indicators, on="date", how="inner", suffixes=("", "_ta"))

    cols_to_drop = [c for c in merged.columns if c in _DROP_COLUMNS or c.rstrip("_ta") in _DROP_COLUMNS]
    merged.drop(columns=cols_to_drop, errors="ignore", inplace=True)

    csv_path = f"/tmp/backtest_{ticker}_{iteration}.csv"
    merged.to_csv(csv_path, index=False)

    csv_columns = [c for c in merged.columns if c != "date"]

    logger.info(
        "Fetcher saved %d rows to %s with columns: %s",
        len(merged),
        csv_path,
        csv_columns,
    )

    return {"csv_path": csv_path, "csv_columns": csv_columns}
