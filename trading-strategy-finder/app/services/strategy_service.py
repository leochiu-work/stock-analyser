from __future__ import annotations

import os
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.repositories import strategy_repository
from app.agents.state import StrategyState
from app.agents.graph import graph

logger = logging.getLogger(__name__)


def run_research(ticker: str, db: Session, max_iterations: int) -> list[Strategy]:
    existing = strategy_repository.get_running_by_ticker(db, ticker)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A research run is already in progress for ticker '{ticker}'.",
        )

    previous_hypotheses: list[str] = []
    rejection_reasons: list[str] = []
    csv_paths: list[str] = []
    results: list[Strategy] = []

    for iteration in range(max_iterations):
        strategy = strategy_repository.create(db, ticker)

        try:
            initial_state: StrategyState = {
                "ticker": ticker,
                "iteration": iteration,
                "rag_context": "",
                "hypothesis": "",
                "previous_hypotheses": previous_hypotheses,
                "rejection_reasons": rejection_reasons,
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
            }

            final_state: StrategyState = graph.invoke(initial_state)

            if csv_path := final_state.get("csv_path"):
                csv_paths.append(csv_path)

            stats = final_state.get("execution_stats") or {}
            approved = final_state.get("approved", False)

            strategy = strategy_repository.update(
                db,
                strategy.id,
                hypothesis=final_state.get("hypothesis"),
                sharpe_ratio=stats.get("Sharpe Ratio"),
                total_return_pct=stats.get("Return [%]"),
                max_drawdown_pct=stats.get("Max. Drawdown [%]"),
                win_rate_pct=stats.get("Win Rate [%]"),
                num_trades=stats.get("# Trades"),
                ai_evaluation=final_state.get("ai_evaluation"),
                ai_score=final_state.get("ai_score"),
                approved=approved,
                rejection_reason=final_state.get("rejection_reason"),
                raw_output=stats,
                status="completed" if approved else "failed",
            )

        except Exception as exc:
            logger.exception(
                "Agent graph failed for ticker %s iteration %d: %s",
                ticker, iteration, exc,
            )
            strategy_repository.update(db, strategy.id, status="failed")
            results.append(strategy)
            raise

        results.append(strategy)

        if hyp := final_state.get("hypothesis"):
            previous_hypotheses = previous_hypotheses + [hyp]
        if not approved and (r := final_state.get("rejection_reason")):
            rejection_reasons = rejection_reasons + [r]

        if approved:
            break

    for path in csv_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                logger.warning("Failed to remove temp CSV: %s", path)

    return results
