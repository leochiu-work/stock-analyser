from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class BacktestResultResponse(BaseModel):
    id: uuid.UUID
    strategy_id: uuid.UUID
    sharpe_ratio: float | None
    total_return_pct: float | None
    max_drawdown_pct: float | None
    win_rate_pct: float | None
    num_trades: int | None
    backtest_start: date | None
    backtest_end: date | None
    ai_evaluation: str | None
    ai_score: float | None
    approved: bool
    rejection_reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
