from langgraph.graph import StateGraph, END
from app.agents.state import StrategyState
from app.agents.nodes import researcher, fetcher, coder, executor, evaluator

_MAX_CODE_FIX_RETRIES = 3


def _route_after_executor(state: StrategyState) -> str:
    if state.get("code_error") and state.get("code_fix_retries", 0) < _MAX_CODE_FIX_RETRIES:
        return "coder"
    return "evaluator"


def _route_after_evaluator(state: StrategyState) -> str:
    if state["approved"] or state["iteration"] >= state["max_iterations"]:
        return END
    return "researcher"


builder = StateGraph(StrategyState)
builder.add_node("researcher", researcher.run)
builder.add_node("fetcher", fetcher.run)
builder.add_node("coder", coder.run)
builder.add_node("executor", executor.run)
builder.add_node("evaluator", evaluator.run)
builder.set_entry_point("researcher")
builder.add_edge("researcher", "fetcher")
builder.add_edge("fetcher", "coder")
builder.add_edge("coder", "executor")
builder.add_conditional_edges("executor", _route_after_executor)
builder.add_conditional_edges("evaluator", _route_after_evaluator)
graph = builder.compile()
