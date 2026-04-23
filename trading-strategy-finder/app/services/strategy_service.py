from __future__ import annotations

import os
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.strategy import Strategy
from app.repositories import strategy_repository, backtest_repository
from app.agents.state import StrategyState
from app.agents.graph import graph

logger = logging.getLogger(__name__)


def run_research(ticker: str, db: Session) -> Strategy:
    existing = strategy_repository.get_running_by_ticker(db, ticker)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A research run is already in progress for ticker '{ticker}'.",
        )

    strategy = strategy_repository.create(db, ticker)

    initial_state: StrategyState = {
        "ticker": ticker,
        "iteration": 0,
        "max_iterations": settings.max_research_iterations,
        "rag_context": "",
        "hypothesis": "",
        "previous_hypotheses": [],
        "rejection_reasons": [],
        "csv_path": "",
        "csv_columns": [],
        "strategy_path": "",
        "code_error": "",
        "code_fix_retries": 0,
        "execution_stats": {},
        "ai_score": 0.0,
        "ai_evaluation": "",
        "approved": False,
        "rejection_reason": None,
        "best_result": None,
    }

    try:
        final_state: StrategyState = graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Agent graph failed for ticker %s: %s", ticker, exc)
        strategy_repository.update(db, strategy.id, status="failed", iterations=0)
        raise

    if final_state.get("best_result"):
        best = final_state["best_result"]
        backtest_repository.create(
            db,
            strategy_id=strategy.id,
            sharpe_ratio=best.get("sharpe_ratio"),
            total_return_pct=best.get("total_return_pct"),
            max_drawdown_pct=best.get("max_drawdown_pct"),
            win_rate_pct=best.get("win_rate_pct"),
            num_trades=best.get("num_trades"),
            backtest_start=best.get("backtest_start"),
            backtest_end=best.get("backtest_end"),
            ai_evaluation=best.get("ai_evaluation"),
            ai_score=best.get("ai_score"),
            approved=best.get("approved", False),
            rejection_reason=best.get("rejection_reason"),
            raw_output=best.get("execution_stats"),
        )

    final_status = "completed" if final_state.get("approved") else "failed"
    strategy = strategy_repository.update(
        db,
        strategy.id,
        status=final_status,
        iterations=final_state.get("iteration", 0),
    )

    csv_path = final_state.get("csv_path", "")
    if csv_path and os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except OSError:
            logger.warning("Failed to remove temp CSV: %s", csv_path)

    return strategy
