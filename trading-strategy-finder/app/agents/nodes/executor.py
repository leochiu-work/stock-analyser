from __future__ import annotations

import json
import logging

import e2b_code_interpreter
from e2b.sandbox.commands.command_handle import CommandExitException

from app.agents.state import StrategyState
from app.config import settings

logger = logging.getLogger(__name__)

_WRAPPER_SCRIPT = """
import json
import pandas as pd
from backtesting import Backtest

# Load data — wrapper owns this; strategy.py only defines the class
data = pd.read_csv("data.csv", index_col="date", parse_dates=True)

# backtesting.py requires ascending date order
data = data.sort_index(ascending=True)

# backtesting.py requires title-cased OHLCV column names
rename_map = {c: c.capitalize() for c in ("open", "high", "low", "close", "volume")}
data = data.rename(columns={k: v for k, v in rename_map.items() if k in data.columns})

# Inject TradingStrategy class into this module's global scope
exec(open("strategy.py").read(), globals())

bt = Backtest(data, TradingStrategy, cash=10_000, commission=0.002)
stats = bt.run()

stats.drop(["_strategy", "_equity_curve", "_trades"], inplace=True)
output = json.loads(stats.to_json())

# output = {}
# for k, v in stats.items():
#     if pd.isna(v):
#         output[k] = None
#     else:
#         try:
#             output[k] = float(v)
#         except (TypeError, ValueError):
#             output[k] = str(v)

print(json.dumps(output))
"""


def run(state: StrategyState) -> dict:
    sandbox = e2b_code_interpreter.Sandbox.create(
        timeout=settings.e2b_timeout_seconds,
        api_key=settings.e2b_api_key or None,
    )

    try:
        sandbox.commands.run("pip install backtesting pandas --quiet")

        with open(state["csv_path"], "rb") as f:
            sandbox.files.write("data.csv", f)

        with open(state["strategy_path"], "rb") as f:
            sandbox.files.write("strategy.py", f)
        logger.info("Executor uploading strategy from %s", state["strategy_path"])
        sandbox.files.write("wrapper.py", _WRAPPER_SCRIPT.encode())

        try:
            result = sandbox.commands.run("python wrapper.py")
            stdout = result.stdout.strip()
            try:
                execution_stats = json.loads(stdout)
            except json.JSONDecodeError:
                logger.warning("Executor: failed to parse stdout as JSON: %s", stdout)
                execution_stats = {"error": stdout}
            code_error = ""
        except CommandExitException as exc:
            logger.warning("Executor: sandbox command failed: %s", str(exc))
            execution_stats = {}
            code_error = str(exc)

    finally:
        sandbox.kill()

    if code_error:
        logger.info("Executor returning code error for coder to fix")
        return {"execution_stats": {}, "code_error": code_error}

    logger.info("Executor finished. Stats keys: %s", list(execution_stats.keys()))
    return {"execution_stats": execution_stats, "code_error": ""}
