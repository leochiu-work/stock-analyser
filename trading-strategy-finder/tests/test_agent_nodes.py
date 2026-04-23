"""Tests for each agent node in isolation with mocked dependencies."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch, call

import pandas as pd
import pytest

from app.agents.state import StrategyState


def _base_state(**overrides) -> StrategyState:
    state: StrategyState = {
        "ticker": "AAPL",
        "iteration": 0,
        "max_iterations": 3,
        "rag_context": "",
        "hypothesis": "Buy when RSI < 30, sell when RSI > 70.",
        "previous_hypotheses": [],
        "rejection_reasons": [],
        "csv_path": "",
        "csv_columns": ["open", "high", "low", "close", "rsi", "macd"],
        "strategy_path": "",
        "code_error": "",
        "code_fix_retries": 0,
        "execution_stats": {},
        "ai_score": 0.0,
        "ai_evaluation": "",
        "approved": False,
        "rejection_reason": None,
        "best_result": None,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# researcher node
# ---------------------------------------------------------------------------

class TestResearcherNode:
    def test_returns_hypothesis_and_updates_previous(self):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Invest in moats and margin of safety."]],
        }
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Buy quality stocks with low P/E."

        with (
            patch("app.agents.nodes.researcher.get_collection", return_value=mock_collection),
            patch("app.agents.nodes.researcher.OllamaLLM", return_value=mock_llm_instance),
        ):
            from app.agents.nodes import researcher
            state = _base_state(previous_hypotheses=["Old hypothesis"])
            result = researcher.run(state)

        assert "hypothesis" in result
        assert result["hypothesis"] == "Buy quality stocks with low P/E."
        assert len(result["previous_hypotheses"]) == 2
        assert "Old hypothesis" in result["previous_hypotheses"]

    def test_rejection_reasons_appear_in_prompt(self):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"documents": [["Some context."]]}
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "New hypothesis."

        with (
            patch("app.agents.nodes.researcher.get_collection", return_value=mock_collection),
            patch("app.agents.nodes.researcher.OllamaLLM", return_value=mock_llm_instance),
        ):
            from app.agents.nodes import researcher
            state = _base_state(rejection_reasons=["Sharpe ratio too low", "Not enough trades"])
            researcher.run(state)

        prompt_arg = mock_llm_instance.invoke.call_args[0][0]
        assert "Sharpe ratio too low" in prompt_arg
        assert "Not enough trades" in prompt_arg

    def test_rag_context_included(self):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Document A", "Document B"]],
        }
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Hypothesis."

        with (
            patch("app.agents.nodes.researcher.get_collection", return_value=mock_collection),
            patch("app.agents.nodes.researcher.OllamaLLM", return_value=mock_llm_instance),
        ):
            from app.agents.nodes import researcher
            result = researcher.run(_base_state())

        assert "Document A" in result["rag_context"]
        assert "Document B" in result["rag_context"]


# ---------------------------------------------------------------------------
# fetcher node
# ---------------------------------------------------------------------------

class TestFetcherNode:
    def test_writes_csv_and_returns_columns(self):
        prices = [
            {"date": "2023-01-01", "ticker": "AAPL", "open": 100.0, "close": 105.0},
            {"date": "2023-01-02", "ticker": "AAPL", "open": 105.0, "close": 110.0},
        ]
        indicators = [
            {"date": "2023-01-01", "ticker": "AAPL", "rsi": 45.0, "macd": 0.5},
            {"date": "2023-01-02", "ticker": "AAPL", "rsi": 55.0, "macd": 0.8},
        ]

        with (
            patch("app.agents.nodes.fetcher.price_client.get_prices", return_value=prices),
            patch("app.agents.nodes.fetcher.ta_client.get_indicators", return_value=indicators),
        ):
            from app.agents.nodes import fetcher
            state = _base_state(ticker="AAPL", iteration=0)
            result = fetcher.run(state)

        assert result["csv_path"] == "/tmp/backtest_AAPL_0.csv"
        assert os.path.exists(result["csv_path"])
        assert "date" not in result["csv_columns"]
        assert "ticker" not in result["csv_columns"]
        assert "open" in result["csv_columns"]
        assert "rsi" in result["csv_columns"]

        # Clean up
        os.remove(result["csv_path"])

    def test_csv_columns_excludes_date(self):
        prices = [{"date": "2023-01-01", "open": 100.0, "close": 105.0}]
        indicators = [{"date": "2023-01-01", "sma_20": 98.0}]

        with (
            patch("app.agents.nodes.fetcher.price_client.get_prices", return_value=prices),
            patch("app.agents.nodes.fetcher.ta_client.get_indicators", return_value=indicators),
        ):
            from app.agents.nodes import fetcher
            result = fetcher.run(_base_state())

        assert "date" not in result["csv_columns"]
        assert "sma_20" in result["csv_columns"]

        if os.path.exists(result["csv_path"]):
            os.remove(result["csv_path"])


# ---------------------------------------------------------------------------
# coder node
# ---------------------------------------------------------------------------

class TestCoderNode:
    def test_prompt_contains_csv_columns(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = '```python\nfrom backtesting import Strategy\nclass TradingStrategy(Strategy):\n    def init(self): pass\n    def next(self): pass\n```'

        with patch("app.agents.nodes.coder.OllamaLLM", return_value=mock_llm):
            from app.agents.nodes import coder
            state = _base_state(csv_columns=["open", "high", "rsi"])
            result = coder.run(state)

        prompt = mock_llm.invoke.call_args[0][0]
        assert "open" in prompt
        assert "rsi" in prompt
        assert "strategy_path" in result
        assert result["strategy_path"].endswith(".py")

    def test_extracts_code_from_fenced_block(self):
        code = 'from backtesting import Strategy\nclass TradingStrategy(Strategy):\n    def init(self): pass\n    def next(self): pass'
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = f"Here is the code:\n```python\n{code}\n```"

        with patch("app.agents.nodes.coder.OllamaLLM", return_value=mock_llm):
            from app.agents.nodes import coder
            result = coder.run(_base_state())

        assert result["strategy_path"].endswith(".py")
        with open(result["strategy_path"]) as f:
            assert f.read() == code

    def test_strategy_written_to_file(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = '```python\nfrom backtesting import Strategy\nclass TradingStrategy(Strategy):\n    def init(self): pass\n    def next(self): pass\n```'

        with patch("app.agents.nodes.coder.OllamaLLM", return_value=mock_llm):
            from app.agents.nodes import coder
            result = coder.run(_base_state())

        assert os.path.exists(result["strategy_path"])
        with open(result["strategy_path"]) as f:
            content = f.read()
        assert "TradingStrategy" in content


# ---------------------------------------------------------------------------
# executor node
# ---------------------------------------------------------------------------

class TestExecutorNode:
    def test_uploads_files_and_returns_stats(self):
        stats = {"Sharpe Ratio": 1.2, "Return [%]": 25.0, "# Trades": 12}

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(stats)

        mock_sandbox = MagicMock()
        mock_sandbox.commands.run.return_value = mock_result

        with (
            tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as csv_f,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as py_f,
        ):
            csv_f.write(b"date,open,close\n2023-01-01,100,105\n")
            csv_path = csv_f.name
            py_f.write("class TradingStrategy: pass")
            strategy_path = py_f.name

        try:
            with patch("app.agents.nodes.executor.e2b_code_interpreter.Sandbox", return_value=mock_sandbox):
                from app.agents.nodes import executor
                state = _base_state(csv_path=csv_path, strategy_path=strategy_path)
                result = executor.run(state)

            assert result["execution_stats"]["Sharpe Ratio"] == 1.2
            assert mock_sandbox.files.write.called
        finally:
            os.unlink(csv_path)
            os.unlink(strategy_path)
            mock_sandbox.kill.assert_called_once()

    def test_sandbox_killed_even_on_error(self):
        mock_sandbox = MagicMock()
        mock_sandbox.commands.run.side_effect = RuntimeError("Sandbox error")

        with (
            tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as csv_f,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as py_f,
        ):
            csv_f.write(b"date,open,close\n2023-01-01,100,105\n")
            csv_path = csv_f.name
            py_f.write("class TradingStrategy: pass")
            strategy_path = py_f.name

        try:
            with patch("app.agents.nodes.executor.e2b_code_interpreter.Sandbox", return_value=mock_sandbox):
                from app.agents.nodes import executor
                with pytest.raises(RuntimeError):
                    executor.run(_base_state(csv_path=csv_path, strategy_path=strategy_path))
            mock_sandbox.kill.assert_called_once()
        finally:
            os.unlink(csv_path)
            os.unlink(strategy_path)


# ---------------------------------------------------------------------------
# evaluator node
# ---------------------------------------------------------------------------

class TestEvaluatorNode:
    def _run_evaluator(self, llm_response: str, state_overrides: dict = None):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = llm_response

        with patch("app.agents.nodes.evaluator.OllamaLLM", return_value=mock_llm):
            from app.agents.nodes import evaluator
            state = _base_state(**(state_overrides or {}))
            state["execution_stats"] = {
                "Sharpe Ratio": 0.8,
                "Return [%]": 15.0,
                "Max. Drawdown [%]": -20.0,
                "Win Rate [%]": 55.0,
                "# Trades": 20,
            }
            return evaluator.run(state)

    def test_approval_path(self):
        response = json.dumps({
            "score": 8.5,
            "approved": True,
            "reason": "All criteria met",
            "qualitative_evaluation": "Excellent risk-adjusted returns.",
        })
        result = self._run_evaluator(response)
        assert result["approved"] is True
        assert result["ai_score"] == 8.5
        assert result["rejection_reason"] is None

    def test_rejection_path(self):
        response = json.dumps({
            "score": 3.0,
            "approved": False,
            "reason": "Sharpe ratio too low",
            "qualitative_evaluation": "Strategy underperforms.",
        })
        result = self._run_evaluator(response)
        assert result["approved"] is False
        assert result["rejection_reason"] == "Sharpe ratio too low"
        assert "Sharpe ratio too low" in result["rejection_reasons"]

    def test_iteration_incremented(self):
        response = json.dumps({
            "score": 5.0,
            "approved": False,
            "reason": "Mediocre",
            "qualitative_evaluation": "OK.",
        })
        result = self._run_evaluator(response, {"iteration": 1})
        assert result["iteration"] == 2

    def test_best_result_updated_when_score_is_higher(self):
        response = json.dumps({
            "score": 9.0,
            "approved": True,
            "reason": "Great",
            "qualitative_evaluation": "Excellent.",
        })
        previous_best = {"ai_score": 4.0}
        result = self._run_evaluator(response, {"best_result": previous_best})
        assert result["best_result"]["ai_score"] == 9.0

    def test_best_result_not_updated_when_score_is_lower(self):
        response = json.dumps({
            "score": 2.0,
            "approved": False,
            "reason": "Poor",
            "qualitative_evaluation": "Bad.",
        })
        previous_best = {"ai_score": 7.0}
        result = self._run_evaluator(response, {"best_result": previous_best})
        assert result["best_result"]["ai_score"] == 7.0


# ---------------------------------------------------------------------------
# Graph integration test
# ---------------------------------------------------------------------------

class TestGraphIntegration:
    def test_graph_rejects_twice_then_approves(self):
        """Mock all LLM/external calls. Reject iterations 0 and 1, approve iteration 2.

        The evaluator LLM is mocked to return rejection JSON twice, then approval JSON.
        All other external calls (ChromaDB, price/TA clients, E2B sandbox) are also mocked.
        """
        call_count = {"n": 0}

        def evaluator_llm_invoke(prompt):
            call_count["n"] += 1
            if call_count["n"] >= 3:
                return json.dumps({
                    "score": 8.5,
                    "approved": True,
                    "reason": "All criteria met",
                    "qualitative_evaluation": "Strong strategy.",
                })
            return json.dumps({
                "score": 2.0,
                "approved": False,
                "reason": "Sharpe ratio too low",
                "qualitative_evaluation": "Weak strategy.",
            })

        mock_researcher_llm = MagicMock()
        mock_researcher_llm.invoke.return_value = "Buy when RSI < 30."

        mock_coder_llm = MagicMock()
        mock_coder_llm.invoke.return_value = '```python\nimport pandas as pd\nfrom backtesting import Strategy\ndata = pd.read_csv("data.csv", index_col="date", parse_dates=True)\nclass TradingStrategy(Strategy):\n    def init(self): pass\n    def next(self): pass\n```'

        mock_evaluator_llm = MagicMock()
        mock_evaluator_llm.invoke.side_effect = evaluator_llm_invoke

        mock_sandbox = MagicMock()
        mock_sandbox.commands.run.return_value = MagicMock(
            stdout=json.dumps({"Sharpe Ratio": 0.8, "Return [%]": 10.0, "# Trades": 8})
        )

        prices = [{"date": "2023-01-01", "open": 100.0, "close": 105.0}]
        indicators = [{"date": "2023-01-01", "rsi": 45.0}]

        def make_llm(model, base_url):
            # Return different mocks based on call context by tracking invocation order
            # We use a simple approach: researcher and coder both call OllamaLLM
            # We differentiate by patching each module's OllamaLLM import separately
            return mock_evaluator_llm

        with (
            patch("app.agents.nodes.researcher.get_collection", return_value=MagicMock(
                query=MagicMock(return_value={"documents": [["context"]]})
            )),
            patch("app.agents.nodes.researcher.OllamaLLM", return_value=mock_researcher_llm),
            patch("app.agents.nodes.fetcher.price_client.get_prices", return_value=prices),
            patch("app.agents.nodes.fetcher.ta_client.get_indicators", return_value=indicators),
            patch("app.agents.nodes.coder.OllamaLLM", return_value=mock_coder_llm),
            patch("app.agents.nodes.executor.e2b_code_interpreter.Sandbox", return_value=mock_sandbox),
            patch("app.agents.nodes.evaluator.OllamaLLM", return_value=mock_evaluator_llm),
        ):
            from app.agents.graph import graph

            initial_state: StrategyState = {
                "ticker": "AAPL",
                "iteration": 0,
                "max_iterations": 3,
                "rag_context": "",
                "hypothesis": "",
                "previous_hypotheses": [],
                "rejection_reasons": [],
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
                "best_result": None,
            }
            final_state = graph.invoke(initial_state)

        # Clean up any temp CSV files
        for i in range(4):
            path = f"/tmp/backtest_AAPL_{i}.csv"
            if os.path.exists(path):
                os.remove(path)

        assert final_state["iteration"] == 3
        assert final_state["approved"] is True
        assert final_state["best_result"] is not None
        assert final_state["best_result"]["ai_score"] == 8.5
