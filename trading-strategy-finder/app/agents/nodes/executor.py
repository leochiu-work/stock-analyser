from __future__ import annotations

import json
import logging

import e2b_code_interpreter

from app.agents.state import StrategyState
from app.config import settings

logger = logging.getLogger(__name__)

_WRAPPER_SCRIPT = """
import json
import sys
from backtesting import Backtest

# strategy.py defines TradingStrategy and data
exec(open("strategy.py").read())

bt = Backtest(data, TradingStrategy, cash=10_000, commission=0.002)
stats = bt.run()

output = {}
for k, v in stats.items():
    try:
        output[k] = float(v)
    except (TypeError, ValueError):
        output[k] = str(v)

print(json.dumps(output))
"""


def run(state: StrategyState) -> dict:
    sandbox = e2b_code_interpreter.Sandbox(timeout=settings.e2b_timeout_seconds)

    try:
        sandbox.commands.run("pip install backtesting pandas --quiet")

        with open(state["csv_path"], "rb") as f:
            sandbox.files.write("data.csv", f)

        sandbox.files.write("strategy.py", state["generated_code"].encode())
        sandbox.files.write("wrapper.py", _WRAPPER_SCRIPT.encode())

        result = sandbox.commands.run("python wrapper.py")
        stdout = result.stdout.strip()

        try:
            execution_stats = json.loads(stdout)
        except json.JSONDecodeError:
            logger.warning("Executor: failed to parse stdout as JSON: %s", stdout[:500])
            execution_stats = {"error": stdout}

    finally:
        sandbox.kill()

    logger.info("Executor finished. Stats keys: %s", list(execution_stats.keys()))

    return {"execution_stats": execution_stats}
