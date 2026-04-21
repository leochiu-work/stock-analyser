from datetime import date

from pydantic import BaseModel, ConfigDict


class TAIndicatorResponse(BaseModel):
    ticker: str
    date: date
    sma_20: float | None
    sma_50: float | None
    sma_200: float | None
    ema_12: float | None
    ema_26: float | None
    rsi_14: float | None
    macd_line: float | None
    macd_signal: float | None
    macd_hist: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    atr_14: float | None
    stoch_k: float | None
    stoch_d: float | None

    model_config = ConfigDict(from_attributes=True)


class TAIndicatorListResponse(BaseModel):
    ticker: str
    items: list[TAIndicatorResponse]
