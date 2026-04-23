from __future__ import annotations

import json
import logging
import re

from langchain_ollama import OllamaLLM

from app.agents.state import StrategyState
from app.config import settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"score": 0.0, "approved": False, "reason": "Failed to parse LLM response", "qualitative_evaluation": text}


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
- Number of Trades > 5: sufficient trading activity

Respond with ONLY a JSON object in this exact format:
{{
  "score": <float between 0 and 10>,
  "approved": <true if all rubric criteria met, false otherwise>,
  "reason": "<brief explanation of approval or rejection>",
  "qualitative_evaluation": "<1-2 sentence qualitative assessment>"
}}"""

    llm = OllamaLLM(model=settings.ollama_model, base_url=settings.ollama_base_url)
    response = llm.invoke(prompt)
    parsed = _extract_json(response)

    score = float(parsed.get("score", 0.0))
    approved = bool(parsed.get("approved", False))
    reason = str(parsed.get("reason", ""))
    qualitative = str(parsed.get("qualitative_evaluation", ""))

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
