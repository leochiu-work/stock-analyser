from __future__ import annotations

import uuid
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class StrategyCreate(BaseModel):
    ticker: str


class StrategyResponse(BaseModel):
    id: uuid.UUID
    ticker: str
    hypothesis: str | None = None
    status: str

    # Backtest metrics
    sharpe_ratio: float | None = None
    total_return_pct: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    num_trades: int | None = None
    backtest_start: date | None = None
    backtest_end: date | None = None

    # AI evaluation
    ai_evaluation: str | None = None
    ai_score: float | None = None
    approved: bool = False
    rejection_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
