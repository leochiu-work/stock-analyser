from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.backtest_result import BacktestResult


def create(db: Session, strategy_id: uuid.UUID, **metrics) -> BacktestResult:
    result = BacktestResult(strategy_id=strategy_id, **metrics)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_by_strategy(db: Session, strategy_id: uuid.UUID) -> list[BacktestResult]:
    return (
        db.query(BacktestResult)
        .filter(BacktestResult.strategy_id == strategy_id)
        .order_by(BacktestResult.created_at.desc())
        .all()
    )


def get_best_by_strategy(db: Session, strategy_id: uuid.UUID) -> BacktestResult | None:
    from sqlalchemy import desc, nullslast

    return (
        db.query(BacktestResult)
        .filter(BacktestResult.strategy_id == strategy_id)
        .filter(BacktestResult.ai_score.isnot(None))
        .order_by(desc(BacktestResult.ai_score))
        .first()
    )
