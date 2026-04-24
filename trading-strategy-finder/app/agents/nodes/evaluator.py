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

    logger.info(
        "Evaluator: score=%.2f approved=%s iteration=%d",
        score,
        approved,
        state["iteration"],
    )

    return {
        "ai_score": score,
        "ai_evaluation": qualitative,
        "approved": approved,
        "rejection_reason": reason if not approved else None,
    }
