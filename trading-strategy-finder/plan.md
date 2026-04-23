# Trading Strategy Finder — Implementation Plan

## Directory Structure

```
trading-strategy-finder/
  main.py                          ← FastAPI entry point; API key middleware; include routers
  seed.py                          ← One-time ChromaDB seeder; run at container startup if collection empty
  app/
    config.py                      ← pydantic-settings; all env vars
    database.py                    ← SQLAlchemy engine, SessionLocal, get_db dependency
    chroma.py                      ← ChromaDB HTTP client singleton; get_chroma_collection dependency
    models/
      __init__.py                  ← imports all models for Alembic
      strategy.py                  ← Strategy ORM model
      backtest_result.py           ← BacktestResult ORM model
    repositories/
      strategy_repository.py       ← stateless DB queries for strategies
      backtest_repository.py       ← stateless DB queries for backtest results
    services/
      strategy_service.py          ← orchestrates agent run + DB persistence
      document_service.py          ← add/list/delete ChromaDB documents
      price_client.py              ← httpx client for stock-price-service (OHLCV data only)
      ta_client.py                 ← httpx client for stock-ta-service (indicator data only)
    agents/
      state.py                     ← StrategyState TypedDict (shared graph state)
      graph.py                     ← LangGraph StateGraph definition; compile() called once at startup
      nodes/
        researcher.py              ← RAG lookup → propose hypothesis; receives rejection feedback
        fetcher.py                 ← fetch OHLCV + indicator data → merge → save as local CSV
        coder.py                   ← receive csv_columns from state → generate backtesting.py Strategy class
        executor.py                ← upload CSV + code to E2B sandbox → return stats dict
        evaluator.py               ← score results → approve or reject with structured feedback
    schemas/
      strategy.py                  ← Pydantic request/response models for strategies
      backtest_result.py           ← Pydantic response models for backtest results
      document.py                  ← Pydantic models for /documents endpoints
    routers/
      strategies.py                ← /strategies/* route handlers
      documents.py                 ← /documents/* route handlers
      health.py                    ← /health endpoint
  data/
    seed/                          ← Default investor philosophy text files (.txt / .md)
      warren_buffett.md
      peter_lynch.md
      benjamin_graham.md
  alembic/
    env.py
    versions/
  tests/
    conftest.py                    ← SQLite in-memory + TestClient + mock ChromaDB fixtures
    test_strategy_router.py
    test_document_router.py
    test_strategy_repository.py
    test_backtest_repository.py
    test_agent_nodes.py            ← mocked LLM, E2B, Chroma, and HTTP clients
  Dockerfile
  pyproject.toml
  .env.example
```

## Agent Graph — Loop Design

```
START
  │
  ▼
researcher ──────────────────────────────────────────────┐
  │                                                       │
  ▼                                                       │ (rejected + feedback)
fetcher                                                   │
  │                                                       │
  ▼                                                       │
coder                                                     │
  │                                                       │
  ▼                                                       │
executor                                                  │
  │                                                       │
  ▼                                                       │
evaluator ──── approved ──── END (persist result)        │
  │                                                       │
  └── rejected (iter < MAX) ──────────────────────────────┘
  │
  └── rejected (iter == MAX) ── END (persist best, mark failed)
```

**`StrategyState` fields (TypedDict):**

| Field                  | Type              | Purpose                                                              |
|------------------------|-------------------|----------------------------------------------------------------------|
| `ticker`               | str               | Target ticker for the run                                            |
| `iteration`            | int               | Current loop count (starts at 0)                                     |
| `max_iterations`       | int               | From config; passed into graph at invocation                         |
| `rag_context`          | str               | Retrieved investor philosophy chunks                                 |
| `hypothesis`           | str               | Researcher's proposed strategy description                           |
| `previous_hypotheses`  | list[str]         | Hypotheses from prior iterations; injected into researcher prompt    |
| `rejection_reasons`    | list[str]         | Evaluator feedback from prior rejections                             |
| `csv_path`             | str               | Local filesystem path of the merged CSV written by fetcher           |
| `csv_columns`          | list[str]         | Actual column names present in the CSV; passed to coder              |
| `generated_code`       | str               | Python Strategy class string from coder                              |
| `execution_stats`      | dict              | Raw backtesting.py stats from E2B                                    |
| `ai_score`             | float             | Evaluator numeric score                                              |
| `ai_evaluation`        | str               | Evaluator qualitative text                                           |
| `approved`             | bool              | Evaluator approval flag                                              |
| `rejection_reason`     | str \| None       | Evaluator rejection reason for this iteration                        |
| `best_result`          | dict \| None      | Highest-scoring result across all iterations                         |

## Implementation Steps

1. **Scaffold project**
   - `cd trading-strategy-finder && uv init`
   - Add dependencies:
     ```
     fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic-settings
     langgraph langchain-core ollama chromadb-client
     e2b-code-interpreter backtesting httpx
     pytest pytest-mock pytest-asyncio
     ```
   - Create `.env.example`

2. **Config & environment** (`app/config.py`)
   - `DATABASE_URL`
   - `API_KEY`
   - `OLLAMA_BASE_URL` (default `http://localhost:11434`)
   - `OLLAMA_MODEL` (default `gemma4`)
   - `OLLAMA_EMBED_MODEL` (default `nomic-embed-text`)
   - `E2B_API_KEY`
   - `E2B_TIMEOUT_SECONDS` (default `60`)
   - `CHROMA_HOST`, `CHROMA_PORT` (default `chromadb`, `8000`)
   - `PRICE_SERVICE_BASE_URL`
   - `TA_SERVICE_BASE_URL`
   - `MAX_RESEARCH_ITERATIONS` (default `3`)

3. **Database setup**
   - `app/database.py` — engine + `SessionLocal` + `get_db` (same pattern as existing services)
   - `app/models/strategy.py` — `Strategy` model; `status` as `VARCHAR`; `iterations` as `Integer`
   - `app/models/backtest_result.py` — `BacktestResult` model; `approved` as `Boolean`; `rejection_reason` as `Text` nullable
   - `alembic init alembic` → configure `env.py`
   - First migration: `uv run alembic revision --autogenerate -m "create strategies and backtest_results tables"`

4. **ChromaDB client** (`app/chroma.py`)
   - Create a `chromadb.HttpClient(host, port)` singleton
   - `get_chroma_collection()` — returns (or creates) the `investor_philosophies` collection
   - Embedding function: `OllamaEmbeddingFunction(url=settings.OLLAMA_BASE_URL, model_name=settings.OLLAMA_EMBED_MODEL)`

5. **Seed script** (`seed.py`)
   - On startup, check if `investor_philosophies` collection has any documents
   - If empty, read files from `data/seed/`, chunk them (e.g. 512-token chunks with 50-token overlap), and upsert into ChromaDB with metadata (`investor`, `source`, `chunk_index`)
   - Called from `main.py` lifespan event: `asyncio.to_thread(seed_if_empty)`

6. **Repository layer**
   - `strategy_repository.py`: `create`, `get_by_id`, `get_running_by_ticker`, `list_all` (ticker/status filters), `update`, `delete`
   - `backtest_repository.py`: `create`, `list_by_strategy`, `get_best_by_strategy` (highest `ai_score`)

7. **External API clients**
   - `price_client.py`:
     - `get_prices(ticker, start_date, end_date) -> list[dict]` — fetches OHLCV rows from `GET /api/v1/stocks/{ticker}`
   - `ta_client.py`:
     - `get_indicators(ticker, start_date, end_date) -> list[dict]` — fetches indicator rows from `GET /api/v1/ta/{ticker}`
   - Both use `httpx.Client` (sync; called from fetcher node)

8. **LangGraph agent nodes**

   **`nodes/researcher.py`**
   - Query ChromaDB with the ticker + investment goal as the query string; retrieve top-K philosophy chunks
   - Build prompt including: retrieved context, `previous_hypotheses`, `rejection_reasons`
   - Call Ollama → produce a strategy hypothesis string
   - Update state: `rag_context`, `hypothesis`, append to `previous_hypotheses`

   **`nodes/fetcher.py`**
   - Compute date range: `end_date = today`, `start_date = today - BACKTEST_YEARS years`
   - Call `price_client.get_prices(ticker, start_date, end_date)` → OHLCV list
   - Call `ta_client.get_indicators(ticker, start_date, end_date)` → indicator list
   - Load both into pandas DataFrames; merge on `date` (inner join)
   - Drop non-feature columns (`ticker`, `id`, `created_at`, etc.); keep `date` + numeric columns
   - Save merged DataFrame to `/tmp/backtest_{ticker}_{iteration}.csv`
   - Update state: `csv_path` (the file path), `csv_columns` (list of column names in the CSV, excluding `date`)

   **`nodes/coder.py`**
   - Build prompt: `hypothesis` + `csv_columns` (exact column names available)
   - Tell the LLM the code must read its data from `data.csv` using `pd.read_csv("data.csv", index_col="date", parse_dates=True)`
   - Call Ollama → extract Python code block → set `generated_code`
   - No external HTTP calls; all needed context is already in state

   **`nodes/executor.py`**
   - Create an E2B `Sandbox(timeout=settings.e2b_timeout_seconds)`; install `backtesting` inside it
   - Upload `state["csv_path"]` into the sandbox as `data.csv`
   - Upload `generated_code` as `strategy.py`
   - Write and run a wrapper script: imports the strategy class, runs `bt = Backtest(...); stats = bt.run()`, prints `json.dumps(stats_dict)` to stdout
   - Parse stdout → update state: `execution_stats`
   - Close sandbox in a `finally` block

   **`nodes/evaluator.py`**
   - Build prompt: `execution_stats` + evaluation rubric
   - Call Ollama → parse structured output (score 0–10, approved bool, reason text)
   - Update state: `ai_score`, `ai_evaluation`, `approved`, `rejection_reason`
   - If `ai_score > best_result["ai_score"]` (or `best_result` is None): update `best_result`
   - Increment `iteration`

   **`agents/graph.py`**
   - `StateGraph(StrategyState)` with nodes: `researcher`, `fetcher`, `coder`, `executor`, `evaluator`
   - Edges: `researcher → fetcher → coder → executor → evaluator`
   - Conditional edge from `evaluator`: if `approved` or `iteration >= max_iterations` → `END`; else → `researcher`
   - `graph = builder.compile()` (module-level singleton)

9. **Service layer** (`services/strategy_service.py`)
   - `run_research(ticker, db)`:
     1. Check `strategy_repository.get_running_by_ticker(ticker)` — return if found (409)
     2. `strategy_repository.create(ticker, status="running")`
     3. Build initial `StrategyState`: `ticker`, `iteration=0`, `max_iterations=settings.max_research_iterations`, empty lists for `previous_hypotheses`/`rejection_reasons`, `approved=False`, `best_result=None`
     4. Invoke `graph.invoke(initial_state)` — fetcher runs inside the graph on every iteration
     5. For each backtest result stored in `state["best_result"]` (and intermediate results if tracked), call `backtest_repository.create(...)`
     6. If `state["approved"]`: `update(status="completed")`; else `update(status="failed")`
     7. Update `strategy.iterations = state["iteration"]`
     8. Clean up temp CSV: `os.remove(state["csv_path"])` if it exists

   - `document_service.py`: thin wrapper over `get_chroma_collection()` for add/list/delete

10. **Routers**
    - `routers/strategies.py`: all `/strategies/*` endpoints; `Depends(get_db)`
    - `routers/documents.py`: all `/documents/*` endpoints; `Depends(get_chroma_collection)`
    - `routers/health.py`: `GET /health → {"status": "ok"}`
    - `main.py`: API key middleware (skip `/health`); include all routers; lifespan hook runs `seed.py`

11. **Tests**
    - `conftest.py`:
      - SQLite in-memory engine with `StaticPool`; override `get_db`
      - Mock `get_chroma_collection` to return an in-memory stub
      - `TestClient` fixture
    - `test_agent_nodes.py`: patch `ollama.Client`, `e2b.Sandbox`, `chromadb.HttpClient`, and `httpx.AsyncClient`; assert correct state transitions and loop behaviour (including rejection loop)
    - `test_strategy_router.py`: mock `strategy_service.run_research`; assert 200/409 on duplicate running ticker
    - `test_document_router.py`: mock `document_service`; assert CRUD responses

12. **Dockerfile**
    ```dockerfile
    FROM python:3.12-slim
    WORKDIR /app
    RUN pip install uv
    COPY pyproject.toml .
    RUN uv sync --no-dev
    COPY . .
    EXPOSE 8000
    CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

13. **docker-compose additions**
    Add both ChromaDB and the new service to `docker-compose.yaml`:
    ```yaml
    chromadb:
      image: chromadb/chroma:latest
      ports:
        - "8007:8000"
      volumes:
        - chroma_data:/chroma/chroma

    trading-strategy-finder:
      build: ./trading-strategy-finder
      ports:
        - "8006:8000"
      env_file: ./trading-strategy-finder/.env
      depends_on:
        - postgres
        - chromadb

    volumes:
      chroma_data:
    ```

14. **PostgreSQL init**
    Append to `postgres/init.sql`:
    ```sql
    CREATE DATABASE trading_strategy;
    ```

## Migration Plan

- `uv run alembic revision --autogenerate -m "create strategies and backtest_results tables"`
- `uv run alembic upgrade head`
- UUID PKs: `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)`
- JSONB: `sqlalchemy.dialects.postgresql.JSONB`

## Testing Approach

- SQLite in-memory with `StaticPool` for all DB tests (consistent with existing services)
- UUID and JSONB columns use SQLite-compatible type overrides in test fixtures
- LangGraph graph tested at the node level (unit) and integration level with all external calls mocked
- Rejection loop tested explicitly: mock evaluator to reject N times then approve; assert `iteration` count and correct number of `backtest_results` rows created
- Run: `uv run pytest tests/ -v`

## Open Questions

- **Backtest window:** Configurable via `BACKTEST_YEARS` env var (default `3`). Fetcher computes `start_date = today - BACKTEST_YEARS years`.
- **Ollama availability at startup:** Add a health check in the lifespan hook that confirms Ollama is reachable and the configured models are pulled before accepting requests.
- **Dashboard proxy route:** Add `GET/POST /api/strategies` proxy in `dashboard/src/app/api/strategies/route.ts` pointing to `STRATEGY_SERVICE_BASE_URL` (port 8006).
- **ChromaDB persistence on restart:** The `chroma_data` Docker volume ensures embeddings survive restarts — confirm this is acceptable.
- **Sync vs async graph invocation:** `graph.invoke()` (sync) is simplest since price_client/ta_client are sync httpx; use `asyncio.to_thread(graph.invoke, state)` in the FastAPI endpoint if needed.
- **Intermediate backtest result tracking:** Currently only `best_result` is tracked across iterations. Decide whether to persist every iteration's result or only the best/final one.
