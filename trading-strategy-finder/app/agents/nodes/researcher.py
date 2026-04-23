from __future__ import annotations

import logging

from langchain_ollama import OllamaLLM

from app.agents.state import StrategyState
from app.chroma import get_collection
from app.config import settings

logger = logging.getLogger(__name__)


def run(state: StrategyState) -> dict:
    collection = get_collection()

    query_text = f"{state['ticker']} trading strategy long-term investing"
    results = collection.query(query_texts=[query_text], n_results=5)

    documents = results.get("documents", [[]])[0]
    rag_context = "\n\n".join(documents) if documents else "No relevant documents found."

    previous_hypotheses_text = ""
    if state["previous_hypotheses"]:
        formatted = "\n".join(
            f"- {h}" for h in state["previous_hypotheses"]
        )
        previous_hypotheses_text = f"\n\nPrevious hypotheses to AVOID repeating:\n{formatted}"

    rejection_reasons_text = ""
    if state["rejection_reasons"]:
        formatted = "\n".join(
            f"- {r}" for r in state["rejection_reasons"]
        )
        rejection_reasons_text = f"\n\nPrevious rejection reasons to ADDRESS:\n{formatted}"

    prompt = f"""You are an expert quantitative trading strategist.

Your task is to generate a novel trading strategy hypothesis for the stock ticker: {state['ticker']}.

Reference investment philosophies and approaches:
{rag_context}
{previous_hypotheses_text}
{rejection_reasons_text}

Generate a clear, concise trading strategy hypothesis. The hypothesis should:
1. Specify entry and exit conditions using technical indicators
2. Include risk management rules
3. Be implementable in Python using the backtesting.py library
4. Be different from any previously tested hypotheses

Respond with only the hypothesis description (2-4 sentences):"""

    llm = OllamaLLM(model=settings.ollama_model, base_url=settings.ollama_base_url)
    hypothesis = llm.invoke(prompt).strip()

    logger.info("Researcher generated hypothesis for %s: %s", state["ticker"], hypothesis[:100])

    return {
        "rag_context": rag_context,
        "hypothesis": hypothesis,
        "previous_hypotheses": state["previous_hypotheses"] + [hypothesis],
    }
