# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An AI-powered trading strategy research microservice. A LangGraph multi-agent workflow researches, generates, backtests, and evaluates trading strategies in a feedback loop. Strategies are generated as `backtesting.py` code, executed in an E2B sandbox, and scored by an LLM evaluator. Results persist in PostgreSQL.

## Common Commands

```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Seed ChromaDB with investor philosophy documents
uv run python seed.py

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_agent_nodes.py -v

# Run a single test by name
uv run pytest tests/test_agent_nodes.py::test_researcher_node -v
```

## Architecture

### Agent Graph (`app/agents/`)

The core is a LangGraph `StateGraph` in `graph.py` with five nodes sharing `StrategyState` (TypedDict in `state.py`). Each `graph.invoke()` call produces exactly one strategy and always terminates at the evaluator — there is no loop back inside the graph.

```
researcher → fetcher → coder → executor → evaluator → END
                                    ↓ (code error, retries < 3)
                                  coder (retry)
```

- **researcher**: RAG query to ChromaDB with Ollama embeddings → generates a hypothesis. Receives `rejection_reasons` and `previous_hypotheses` to avoid repeating prior attempts.
- **fetcher**: Calls `stock-price-service` and `stock-ta-service` via HTTP → merges OHLCV + indicators → saves CSV to `/tmp/backtest_{ticker}_{iter}.csv`.
- **coder**: Generates a `TradingStrategy(Strategy)` class for `backtesting.py`. On executor failure, retries up to 3 times with the broken code as context.
- **executor**: Runs code in an E2B sandbox — installs `backtesting`/`pandas`, uploads CSV + strategy files, wraps execution to output JSON stats. Catches `CommandExitException` and returns `code_error` for coder retry.
- **evaluator**: Uses `ChatOllama` with `with_structured_output()` for guaranteed JSON scoring. Sets `approved` flag and `rejection_reason`; always routes to END.

Conditional routing after executor: `code_error` + `code_fix_retries < 3` → coder; else → evaluator.

### Service & Persistence (`app/services/strategy_service.py`)

`run_research()` owns the iteration loop — it calls `graph.invoke()` up to `max_iterations` times, each time producing one strategy. After each invocation it persists the result to PostgreSQL and appends the hypothesis and rejection reason to carry-forward context for the next iteration. If a strategy is approved, the loop breaks early. All strategies (approved or failed) are saved to the DB. Temp CSV files are cleaned up after all iterations complete.

### External Dependencies

| Dependency | Purpose | Config var |
|---|---|---|
| Ollama (local) | LLM reasoning (`gemma3`) + embeddings (`nomic-embed-text`) | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_EMBED_MODEL` |
| ChromaDB | Vector DB for investor philosophy documents | `CHROMA_HOST`, `CHROMA_PORT` |
| E2B | Sandboxed code execution | `E2B_API_KEY`, `E2B_TIMEOUT_SECONDS` |
| stock-price-service | OHLCV data | `PRICE_SERVICE_BASE_URL` |
| stock-ta-service | Technical indicators | `TA_SERVICE_BASE_URL` |
| PostgreSQL | Strategy & backtest result persistence | `DATABASE_URL` |

### Coder Node Constraints

The coder generates code with strict requirements:
- Must inherit `backtesting.py`'s `Strategy` class
- OHLCV access: `self.data.Open/High/Low/Close` (title-cased)
- Indicator access: `self.data['sma_20']` (lowercase, bracket notation)
- CSV loaded with `index_col="date"`, dates parsed — provided by fetcher's `csv_path`

## Testing

Tests use SQLite in-memory with `StaticPool`. `conftest.py` patches PostgreSQL-specific column types (UUID → String, JSONB → JSON). External dependencies (OllamaLLM, E2B Sandbox, ChromaDB, httpx) are patched in each test file.

PostgreSQL-specific upserts are not tested directly — tests insert via ORM and mock `upsert_many` where needed.

## Key Configuration

Copy `.env.example` to `.env`. Critical variables:

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `API_KEY` | `changeme` | `X-API-Key` header (skipped for `/health`) |
| `E2B_API_KEY` | — | Required for sandbox execution |
| `BACKTEST_YEARS` | `3` | Historical data window |
