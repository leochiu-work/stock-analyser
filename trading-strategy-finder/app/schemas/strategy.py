from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.backtest_result import BacktestResultResponse


class StrategyCreate(BaseModel):
    ticker: str


class StrategyResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    description: str | None
    ticker: str
    status: str
    iterations: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyWithResultResponse(StrategyResponse):
    latest_result: BacktestResultResponse | None = None
