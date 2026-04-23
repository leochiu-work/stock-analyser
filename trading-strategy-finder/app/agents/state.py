from __future__ import annotations

from typing import TypedDict


class StrategyState(TypedDict):
    ticker: str
    iteration: int
    max_iterations: int
    rag_context: str
    hypothesis: str
    previous_hypotheses: list[str]
    rejection_reasons: list[str]
    csv_path: str
    csv_columns: list[str]
    generated_code: str
    execution_stats: dict
    ai_score: float
    ai_evaluation: str
    approved: bool
    rejection_reason: str | None
    best_result: dict | None
