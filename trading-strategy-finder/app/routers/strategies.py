from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import strategy_repository
from app.schemas.strategy import StrategyCreate, StrategyResponse
from app.services import strategy_service

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


@router.post("/research", response_model=list[StrategyResponse])
def research_strategy(body: StrategyCreate, db: Session = Depends(get_db)):
    return strategy_service.run_research(ticker=body.ticker.upper(), db=db)


@router.get("/", response_model=list[StrategyResponse])
def list_strategies(
    ticker: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return strategy_repository.list_all(db, ticker=ticker, status=status)


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: uuid.UUID, db: Session = Depends(get_db)):
    strategy = strategy_repository.get_by_id(db, strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found.")
    return strategy


@router.delete("/{strategy_id}", status_code=204)
def delete_strategy(strategy_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted = strategy_repository.delete(db, strategy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Strategy not found.")
