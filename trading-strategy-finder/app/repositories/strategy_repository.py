from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.strategy import Strategy


def create(db: Session, ticker: str) -> Strategy:
    strategy = Strategy(ticker=ticker, status="running")
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def get_by_id(db: Session, id: uuid.UUID) -> Strategy | None:
    return db.query(Strategy).filter(Strategy.id == id).first()


def get_running_by_ticker(db: Session, ticker: str) -> Strategy | None:
    return (
        db.query(Strategy)
        .filter(Strategy.ticker == ticker, Strategy.status == "running")
        .first()
    )


def list_all(
    db: Session,
    ticker: str | None = None,
    status: str | None = None,
) -> list[Strategy]:
    query = db.query(Strategy)
    if ticker is not None:
        query = query.filter(Strategy.ticker == ticker)
    if status is not None:
        query = query.filter(Strategy.status == status)
    return query.order_by(Strategy.created_at.desc()).all()


def update(db: Session, id: uuid.UUID, **kwargs) -> Strategy | None:
    strategy = get_by_id(db, id)
    if strategy is None:
        return None
    for key, value in kwargs.items():
        setattr(strategy, key, value)
    db.commit()
    db.refresh(strategy)
    return strategy


def delete(db: Session, id: uuid.UUID) -> bool:
    strategy = get_by_id(db, id)
    if strategy is None:
        return False
    db.delete(strategy)
    db.commit()
    return True
