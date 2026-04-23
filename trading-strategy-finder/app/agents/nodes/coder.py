from __future__ import annotations

import logging
import re

from langchain_ollama import OllamaLLM

from app.agents.state import StrategyState
from app.config import settings

_STRATEGY_DIR = "/tmp"

logger = logging.getLogger(__name__)


def _extract_code(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


_BASE_REQUIREMENTS = """STRICT REQUIREMENTS:
1. Define ONLY a class named exactly TradingStrategy that inherits from backtesting.Strategy
2. Do NOT load data or import pandas — data is already loaded by the runner
3. Do NOT instantiate Backtest or call bt.run()
4. Implement init(self) to set up indicators using self.I()
5. Implement next(self) with buy/sell logic

IMPORTANT — how to access data inside the Strategy class:
- OHLCV prices: use backtesting.py capitalized properties — self.data.Open, self.data.High, self.data.Low, self.data.Close
- Technical indicator columns: use lowercase dict access — self.data['sma_20'], self.data['rsi_14'], etc.
- NEVER use self.data['close'] or self.data['open'] — the lowercase OHLCV forms do not exist; always use self.data.Close, self.data.Open, etc.

IMPORTANT — _Indicator objects returned by self.I() are NOT pandas Series:
- Do NOT call .shift(), .rolling(), .mean(), .diff(), or any pandas method on them
- To compute a lagged value in next(), use Python indexing: self.my_indicator[-2] (previous bar), self.my_indicator[-1] (current bar)
- To compute rolling/lagged logic, pass a numpy or lambda function into self.I() so the computation happens at init time, not in next()
- crossover() from backtesting.lib works fine with _Indicator objects

Example structure:
```python
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover

class TradingStrategy(Strategy):
    def init(self):
        self.sma20 = self.I(lambda: self.data['sma_20'])
        self.sma50 = self.I(lambda: self.data['sma_50'])

    def next(self):
        if crossover(self.sma20, self.sma50):
            self.buy()
        elif crossover(self.sma50, self.sma20):
            self.sell()
```"""


def run(state: StrategyState) -> dict:
    indicator_cols = [c for c in state["csv_columns"] if c not in ("open", "high", "low", "close", "volume")]
    ohlcv_cols = [c for c in state["csv_columns"] if c in ("open", "high", "low", "close", "volume")]

    code_error = state.get("code_error", "")
    fix_retries = state.get("code_fix_retries", 0)

    if code_error:
        with open(state["strategy_path"]) as f:
            broken_code = f.read()
        prompt = f"""You are an expert Python quantitative trading developer.

The following trading strategy code failed to execute. Fix the error.

Previous (broken) code:
```python
{broken_code}
```

Execution error:
{code_error}

The CSV file contains these OHLCV columns: {", ".join(ohlcv_cols)}
The CSV file also contains these technical indicator columns: {", ".join(indicator_cols)}

{_BASE_REQUIREMENTS}

Provide ONLY the fixed Python code block, no explanation:"""
    else:
        prompt = f"""You are an expert Python quantitative trading developer.

Generate a complete, runnable Python trading strategy using the backtesting.py library.

Trading strategy hypothesis:
{state['hypothesis']}

The CSV file contains these OHLCV columns: {", ".join(ohlcv_cols)}
The CSV file also contains these technical indicator columns: {", ".join(indicator_cols)}

{_BASE_REQUIREMENTS}

Provide ONLY the Python code block, no explanation:"""

    llm = OllamaLLM(model=settings.ollama_model, base_url=settings.ollama_base_url)
    response = llm.invoke(prompt)
    generated_code = _extract_code(response)

    suffix = f"fix{fix_retries + 1}" if code_error else "v0"
    strategy_path = f"{_STRATEGY_DIR}/strategy_{state['ticker']}_{state['iteration']}_{suffix}.py"
    with open(strategy_path, "w") as f:
        f.write(generated_code)
    logger.info("Coder wrote %d chars to %s", len(generated_code), strategy_path)

    return {
        "strategy_path": strategy_path,
        "code_fix_retries": fix_retries + 1 if code_error else 0,
        "code_error": "",
    }
