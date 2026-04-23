from __future__ import annotations

import json
import logging

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from app.agents.state import StrategyState
from app.config import settings

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    score: float = Field(description="Score between 0 and 10")
    approved: bool = Field(description="True if all rubric criteria are met")
    reason: str = Field(description="Brief explanation of approval or rejection")
    qualitative_evaluation: str = Field(description="1-2 sentence qualitative assessment")


def run(state: StrategyState) -> dict:
    stats = state["execution_stats"]
    stats_str = json.dumps(stats, indent=2)

    prompt = f"""You are a quantitative trading strategy evaluator.

Evaluate the following backtesting results for ticker {state['ticker']}:

{stats_str}

Evaluation rubric:
- Sharpe Ratio > 0.5: good risk-adjusted returns
- Total Return > 0%: strategy must be profitable
- Max Drawdown < 50%: acceptable risk exposure
- Number of Trades > 5: sufficient trading activity"""


    logging.info("prompt: %s", prompt)

    llm = ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url)
    structured_llm = llm.with_structured_output(EvaluationResult)
    parsed: EvaluationResult = structured_llm.invoke(prompt)

    score = parsed.score
    approved = parsed.approved
    reason = parsed.reason
    qualitative = parsed.qualitative_evaluation

    current_best = state.get("best_result") or {}
    current_best_score = current_best.get("ai_score", -1) if current_best else -1

    if score > current_best_score:
        best_result = {
            "ai_score": score,
            "ai_evaluation": qualitative,
            "approved": approved,
            "rejection_reason": reason if not approved else None,
            "sharpe_ratio": stats.get("Sharpe Ratio"),
            "total_return_pct": stats.get("Return [%]"),
            "max_drawdown_pct": stats.get("Max. Drawdown [%]"),
            "win_rate_pct": stats.get("Win Rate [%]"),
            "num_trades": stats.get("# Trades"),
            "execution_stats": stats,
        }
    else:
        best_result = current_best

    new_rejection_reasons = list(state["rejection_reasons"])
    if not approved and reason:
        new_rejection_reasons.append(reason)

    logger.info(
        "Evaluator: score=%.2f approved=%s iteration=%d",
        score,
        approved,
        state["iteration"] + 1,
    )

    return {
        "ai_score": score,
        "ai_evaluation": qualitative,
        "approved": approved,
        "rejection_reason": reason if not approved else None,
        "best_result": best_result,
        "iteration": state["iteration"] + 1,
        "rejection_reasons": new_rejection_reasons,
    }
