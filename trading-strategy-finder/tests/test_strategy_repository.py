"""Tests for strategy_repository using SQLite in-memory DB."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.repositories import strategy_repository


def _insert_strategy(
    db: Session,
    ticker: str = "AAPL",
    status: str = "completed",
) -> Strategy:
    s = Strategy(
        id=uuid.uuid4(),
        ticker=ticker,
        status=status,
        iterations=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


class TestStrategyRepository:
    def test_create(self, db: Session):
        s = strategy_repository.create(db, ticker="TSLA")
        assert s.id is not None
        assert s.ticker == "TSLA"
        assert s.status == "running"

    def test_get_by_id_found(self, db: Session):
        inserted = _insert_strategy(db)
        found = strategy_repository.get_by_id(db, inserted.id)
        assert found is not None
        assert found.id == inserted.id

    def test_get_by_id_not_found(self, db: Session):
        result = strategy_repository.get_by_id(db, uuid.uuid4())
        assert result is None

    def test_get_running_by_ticker_found(self, db: Session):
        _insert_strategy(db, ticker="AAPL", status="running")
        found = strategy_repository.get_running_by_ticker(db, "AAPL")
        assert found is not None
        assert found.status == "running"

    def test_get_running_by_ticker_not_found_when_completed(self, db: Session):
        _insert_strategy(db, ticker="AAPL", status="completed")
        found = strategy_repository.get_running_by_ticker(db, "AAPL")
        assert found is None

    def test_list_all_no_filter(self, db: Session):
        _insert_strategy(db, ticker="AAPL")
        _insert_strategy(db, ticker="TSLA")
        results = strategy_repository.list_all(db)
        assert len(results) >= 2

    def test_list_all_filter_by_ticker(self, db: Session):
        _insert_strategy(db, ticker="AAPL")
        _insert_strategy(db, ticker="MSFT")
        results = strategy_repository.list_all(db, ticker="AAPL")
        assert all(s.ticker == "AAPL" for s in results)

    def test_list_all_filter_by_status(self, db: Session):
        _insert_strategy(db, ticker="AAPL", status="completed")
        _insert_strategy(db, ticker="TSLA", status="failed")
        results = strategy_repository.list_all(db, status="completed")
        assert all(s.status == "completed" for s in results)

    def test_update(self, db: Session):
        inserted = _insert_strategy(db)
        updated = strategy_repository.update(db, inserted.id, status="failed", iterations=3)
        assert updated is not None
        assert updated.status == "failed"
        assert updated.iterations == 3

    def test_update_not_found(self, db: Session):
        result = strategy_repository.update(db, uuid.uuid4(), status="failed")
        assert result is None

    def test_delete(self, db: Session):
        inserted = _insert_strategy(db)
        deleted = strategy_repository.delete(db, inserted.id)
        assert deleted is True
        assert strategy_repository.get_by_id(db, inserted.id) is None

    def test_delete_not_found(self, db: Session):
        result = strategy_repository.delete(db, uuid.uuid4())
        assert result is False
