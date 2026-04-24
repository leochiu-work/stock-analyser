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

The core is a LangGraph `StateGraph` in `graph.py` with five nodes sharing `StrategyState` (TypedDict in `state.py`):

```
researcher → fetcher → coder → executor → evaluator
    ↑                              ↓ (code error, retries < 3)
    └──────────────────────────────┘ (rejected, iter < max)
```

- **researcher**: RAG query to ChromaDB with Ollama embeddings → generates a hypothesis. Receives `rejection_reasons` and `previous_hypotheses` to avoid repetition.
- **fetcher**: Calls `stock-price-service` and `stock-ta-service` via HTTP → merges OHLCV + indicators → saves CSV to `/tmp/backtest_{ticker}_{iter}.csv`.
- **coder**: Generates a `TradingStrategy(Strategy)` class for `backtesting.py`. On executor failure, retries up to 3 times with the broken code as context.
- **executor**: Runs code in an E2B sandbox — installs `backtesting`/`pandas`, uploads CSV + strategy files, wraps execution to output JSON stats. Catches `CommandExitException` and returns `code_error` for coder retry.
- **evaluator**: Uses `ChatOllama` with `with_structured_output()` for guaranteed JSON scoring. Tracks `best_result` across iterations by `ai_score`. Appends rejection reasons to state.

Conditional routing after executor: `code_error` + `code_fix_retries < 3` → coder; else → evaluator.  
Conditional routing after evaluator: `approved` or `iteration >= max_iterations` → END; else → researcher.

### Service & Persistence (`app/services/strategy_service.py`)

`run_research()` is the orchestration entry point: checks for conflicts (409 if already running), creates DB record, invokes `graph.invoke()` synchronously, persists `best_result` to `backtest_results`, cleans up temp CSV files, marks strategy as `completed` or `failed`.

Every evaluator pass/fail is stored in `backtest_results` — full iteration history is preserved.

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
