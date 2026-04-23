"""Tests for backtest_repository using SQLite in-memory DB."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.backtest_result import BacktestResult
from app.repositories import backtest_repository


def _insert_strategy(db: Session, ticker: str = "AAPL") -> Strategy:
    s = Strategy(
        id=uuid.uuid4(),
        ticker=ticker,
        status="completed",
        iterations=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _insert_backtest_result(
    db: Session,
    strategy_id: uuid.UUID,
    ai_score: float = 5.0,
    approved: bool = False,
) -> BacktestResult:
    r = BacktestResult(
        id=uuid.uuid4(),
        strategy_id=strategy_id,
        ai_score=ai_score,
        approved=approved,
        created_at=datetime.utcnow(),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


class TestBacktestRepository:
    def test_create(self, db: Session):
        strategy = _insert_strategy(db)
        result = backtest_repository.create(
            db,
            strategy_id=strategy.id,
            ai_score=7.5,
            approved=True,
            sharpe_ratio=1.2,
        )
        assert result.id is not None
        assert result.strategy_id == strategy.id
        assert result.ai_score == 7.5
        assert result.approved is True

    def test_list_by_strategy(self, db: Session):
        strategy = _insert_strategy(db)
        _insert_backtest_result(db, strategy.id, ai_score=3.0)
        _insert_backtest_result(db, strategy.id, ai_score=6.0)
        results = backtest_repository.list_by_strategy(db, strategy.id)
        assert len(results) == 2

    def test_list_by_strategy_empty_for_other_strategy(self, db: Session):
        s1 = _insert_strategy(db, ticker="AAPL")
        s2 = _insert_strategy(db, ticker="TSLA")
        _insert_backtest_result(db, s1.id)
        results = backtest_repository.list_by_strategy(db, s2.id)
        assert results == []

    def test_get_best_by_strategy_returns_highest_score(self, db: Session):
        strategy = _insert_strategy(db)
        _insert_backtest_result(db, strategy.id, ai_score=3.0)
        _insert_backtest_result(db, strategy.id, ai_score=8.5)
        _insert_backtest_result(db, strategy.id, ai_score=5.0)
        best = backtest_repository.get_best_by_strategy(db, strategy.id)
        assert best is not None
        assert best.ai_score == 8.5

    def test_get_best_by_strategy_none_when_empty(self, db: Session):
        strategy = _insert_strategy(db)
        best = backtest_repository.get_best_by_strategy(db, strategy.id)
        assert best is None
