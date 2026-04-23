from __future__ import annotations

import logging
import re

from langchain_ollama import OllamaLLM

from app.agents.state import StrategyState
from app.config import settings

logger = logging.getLogger(__name__)


def _extract_code(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def run(state: StrategyState) -> dict:
    columns_str = ", ".join(state["csv_columns"])

    prompt = f"""You are an expert Python quantitative trading developer.

Generate a complete, runnable Python trading strategy using the backtesting.py library.

Trading strategy hypothesis:
{state['hypothesis']}

Available CSV columns (excluding 'date'): {columns_str}

STRICT REQUIREMENTS:
1. Load data with: pd.read_csv("data.csv", index_col="date", parse_dates=True)
2. Define a class that inherits from backtesting.Strategy
3. Implement the init(self) method to initialise indicators
4. Implement the next(self) method with buy/sell logic
5. Use only the columns listed above
6. The class must be named exactly: TradingStrategy
7. Do NOT instantiate Backtest or call bt.run() — only define the class and load the data

Example structure:
```python
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover

data = pd.read_csv("data.csv", index_col="date", parse_dates=True)

class TradingStrategy(Strategy):
    def init(self):
        # initialise indicators here
        pass

    def next(self):
        # buy/sell logic here
        pass
```

Provide ONLY the Python code block, no explanation:"""

    llm = OllamaLLM(model=settings.ollama_model, base_url=settings.ollama_base_url)
    response = llm.invoke(prompt)
    generated_code = _extract_code(response)

    logger.info("Coder generated %d chars of code", len(generated_code))

    return {"generated_code": generated_code}
