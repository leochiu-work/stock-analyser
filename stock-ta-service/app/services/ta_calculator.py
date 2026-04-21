"""
Pure TA computation using the `ta` library (pure Python, no LLVM/numba).
Takes OHLC records and returns per-row TA indicator dicts.
"""
import logging
import math

import pandas as pd
import ta.momentum
import ta.trend
import ta.volatility

logger = logging.getLogger(__name__)


def _nan_to_none(val) -> float | None:
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        return None
    return float(val)


def compute(symbol: str, ohlc_records: list[dict]) -> list[dict]:
    """
    Compute TA indicators from OHLC records.
    Returns list of dicts with ticker, date, and all indicator columns.
    NaN values are converted to None.
    """
    if not ohlc_records:
        return []

    df = pd.DataFrame(ohlc_records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # SMA
    df["sma_20"] = ta.trend.SMAIndicator(close=close, window=20).sma_indicator()
    df["sma_50"] = ta.trend.SMAIndicator(close=close, window=50).sma_indicator()
    df["sma_200"] = ta.trend.SMAIndicator(close=close, window=200).sma_indicator()

    # EMA
    df["ema_12"] = ta.trend.EMAIndicator(close=close, window=12).ema_indicator()
    df["ema_26"] = ta.trend.EMAIndicator(close=close, window=26).ema_indicator()

    # RSI
    df["rsi_14"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()

    # MACD
    macd = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    df["macd_line"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    # ATR
    df["atr_14"] = ta.volatility.AverageTrueRange(
        high=high, low=low, close=close, window=14
    ).average_true_range()

    # Stochastic
    stoch = ta.momentum.StochasticOscillator(
        high=high, low=low, close=close, window=14, smooth_window=3
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    indicator_cols = [
        "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26",
        "rsi_14",
        "macd_line", "macd_signal", "macd_hist",
        "bb_upper", "bb_middle", "bb_lower",
        "atr_14",
        "stoch_k", "stoch_d",
    ]

    results = []
    for _, row in df.iterrows():
        record: dict = {
            "ticker": symbol.upper(),
            "date": row["date"].date(),
        }
        for col in indicator_cols:
            record[col] = _nan_to_none(row.get(col))
        results.append(record)

    logger.info("Computed %d TA rows for %s", len(results), symbol)
    return results
