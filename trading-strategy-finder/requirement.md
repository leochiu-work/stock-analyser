# Trading Strategy Finder — Requirements

## Overview

`trading-strategy-finder` is an AI agent service that researches, generates, backtests, and evaluates trading strategies on demand. A LangGraph agent team orchestrates the workflow in a loop:

1. **Researcher** — queries a ChromaDB RAG store of famous investor philosophies (Buffett, Lynch, etc.) to propose a strategy hypothesis. The researcher never sees raw data.
2. **Fetcher** — reads the hypothesis and determines what data is needed. Calls `stock-price-service` for OHLCV data and `stock-ta-service` for technical indicators, merges both datasets by date, and saves the result as a local CSV file. Passes the CSV path and the exact column names to the next agent.
3. **Coder** — receives the hypothesis and the list of available CSV columns. Generates a `backtesting.py`-compatible `Strategy` class that reads its data from `data.csv`. Does not call any external services.
4. **Executor** — creates an E2B sandbox, uploads the CSV (as `data.csv`) and the generated code, runs the backtest, and parses the output stats.
5. **Evaluator** — scores the backtest results. If the strategy is rejected, the evaluator sends structured feedback back to the researcher and the loop repeats (up to `MAX_RESEARCH_ITERATIONS` times). If the strategy passes, results are persisted.

Strategies and their backtest metrics are stored in PostgreSQL. ChromaDB (running in Docker) serves as the vector database for the RAG pipeline. Embeddings are generated via the local Ollama `nomic-embed-text` model.

## Consumers & Dependencies

| Direction | Service / Client           | Notes                                                                      |
|-----------|---------------------------|----------------------------------------------------------------------------|
| Inbound   | Next.js dashboard          | Triggers strategy research runs and retrieves stored results via HTTP       |
| Outbound  | stock-price-service        | Fetcher agent calls `GET /api/v1/stocks/{ticker}` for OHLCV data            |
| Outbound  | stock-ta-service           | Fetcher agent calls `GET /api/v1/ta/{ticker}` for technical indicator data  |
| Outbound  | Local Ollama (gemma4)      | LLM inference for researcher, coder, and evaluator agent nodes              |
| Outbound  | Local Ollama (nomic-embed-text) | Embedding model for RAG document retrieval from ChromaDB              |
| Outbound  | ChromaDB                   | Vector database storing investor philosophy documents for RAG               |
| Outbound  | E2B                        | Secure code-execution sandbox for running agent-generated backtest code     |

## Tech Stack

| Layer       | Choice                                                              | Notes                                                        |
|-------------|---------------------------------------------------------------------|--------------------------------------------------------------|
| Language    | Python 3.12+                                                        | Consistent with existing services                            |
| Framework   | FastAPI + LangGraph                                                 | FastAPI for HTTP API; LangGraph for agent workflow with loops |
| Database    | PostgreSQL                                                          | Database name: `trading_strategy`                            |
| Vector DB   | ChromaDB                                                            | Runs as a separate Docker container                          |
| ORM         | SQLAlchemy + Alembic                                                | Consistent with existing services                            |
| Key libs    | `langgraph`, `chromadb`, `ollama`, `e2b-code-interpreter`, `backtesting`, `httpx`, `pydantic-settings` | |

## Database Schema

### `strategies`

| Column        | Type        | Notes                                                        |
|---------------|-------------|--------------------------------------------------------------|
| id            | UUID (PK)   | Auto-generated                                               |
| name          | VARCHAR     | Short human-readable strategy name                           |
| description   | TEXT        | Agent-generated description of the strategy logic            |
| ticker        | VARCHAR     | Ticker symbol the strategy was designed for                  |
| parameters    | JSONB       | Strategy parameters (e.g. window sizes, thresholds)          |
| iterations    | INTEGER     | Number of researcher→evaluator cycles completed              |
| status        | VARCHAR     | `pending`, `running`, `completed`, `failed`                  |
| created_at    | TIMESTAMP   | Row creation time                                            |
| updated_at    | TIMESTAMP   | Last update time                                             |

### `backtest_results`

| Column              | Type        | Notes                                                     |
|---------------------|-------------|-----------------------------------------------------------|
| id                  | UUID (PK)   | Auto-generated                                            |
| strategy_id         | UUID (FK)   | References `strategies.id`                                |
| sharpe_ratio        | FLOAT       | Risk-adjusted return metric                               |
| total_return_pct    | FLOAT       | Total return over backtest period as a percentage         |
| max_drawdown_pct    | FLOAT       | Maximum peak-to-trough drawdown as a percentage           |
| win_rate_pct        | FLOAT       | Percentage of winning trades                              |
| num_trades          | INTEGER     | Total number of trades executed                           |
| backtest_start      | DATE        | Start date of the backtest period                         |
| backtest_end        | DATE        | End date of the backtest period                           |
| ai_evaluation       | TEXT        | Evaluator agent's qualitative assessment                  |
| ai_score            | FLOAT       | Numeric score assigned by evaluator agent (0–10)          |
| approved            | BOOLEAN     | Whether the evaluator approved this result                |
| rejection_reason    | TEXT        | Evaluator's reason for rejection (NULL if approved)       |
| raw_output          | JSONB       | Full backtesting.py stats output for reference            |
| created_at          | TIMESTAMP   | Row creation time                                         |

## RAG / ChromaDB Schema

### Collection: `investor_philosophies`

Each document represents a chunk of text from a famous investor's writings or philosophy.

| Metadata field  | Type    | Notes                                           |
|-----------------|---------|-------------------------------------------------|
| investor        | string  | e.g. `"warren_buffett"`, `"peter_lynch"`        |
| source          | string  | e.g. `"Berkshire Hathaway Letter 2008"`         |
| chunk_index     | integer | Position of this chunk within the source        |

Documents are embedded via Ollama `nomic-embed-text`.

## API Endpoints

| Method | Path                              | Description                                                   | Auth required |
|--------|-----------------------------------|---------------------------------------------------------------|---------------|
| POST   | /strategies/research              | Trigger a strategy research run for a ticker                  | Yes           |
| GET    | /strategies                       | List all strategies (filterable by ticker, status)            | Yes           |
| GET    | /strategies/{strategy_id}         | Get a single strategy with its latest backtest result         | Yes           |
| GET    | /strategies/{strategy_id}/results | List all backtest results (all iterations) for a strategy     | Yes           |
| DELETE | /strategies/{strategy_id}         | Delete a strategy and its backtest results                    | Yes           |
| POST   | /documents                        | Add a philosophy document to ChromaDB for RAG                 | Yes           |
| GET    | /documents                        | List documents in ChromaDB (metadata only)                    | Yes           |
| DELETE | /documents/{document_id}          | Remove a document from ChromaDB                               | Yes           |
| GET    | /health                           | Health check                                                  | No            |

## External Integrations

| API / Service           | Auth method              | Notes                                                                      |
|-------------------------|--------------------------|----------------------------------------------------------------------------|
| Local Ollama (gemma4)   | None (local)             | LLM for researcher, coder, evaluator agents; `OLLAMA_BASE_URL` env var     |
| Local Ollama (nomic-embed-text) | None (local)     | Embedding model for ChromaDB ingestion and retrieval; same Ollama instance |
| E2B                     | API key (`E2B_API_KEY`)  | Sandboxed Python executor; one sandbox created per research run            |
| ChromaDB                | None (internal Docker)   | `CHROMA_HOST` + `CHROMA_PORT` env vars; HTTP client mode                  |
| stock-price-service     | Internal HTTP            | `PRICE_SERVICE_BASE_URL` env var; fetcher calls `GET /api/v1/stocks/{ticker}` |
| stock-ta-service        | Internal HTTP            | `TA_SERVICE_BASE_URL` env var; fetcher calls `GET /api/v1/ta/{ticker}`        |

## Message Queue Events

None. This service is purely HTTP-driven.

## Non-Functional Requirements

- **Host port:** 8006
- **Internal port:** 8000 (FastAPI uvicorn inside container)
- **Idempotency:** A `POST /strategies/research` for a ticker that already has a `running` strategy returns the existing run rather than starting a new one.
- **Research loop:** Researcher → Fetcher → Coder → Executor → Evaluator; if rejected, evaluator returns structured feedback to the researcher and the cycle repeats. The fetcher re-runs on each iteration (same data window; CSV is overwritten). The previous hypotheses and rejection reasons are included in the researcher's context to avoid repetition.
- **Loop limit:** Controlled by `MAX_RESEARCH_ITERATIONS` env var (default: `3`). On exhaustion, the run is marked `failed` and the best intermediate result (highest `ai_score`) is persisted.
- **All intermediate results stored:** Every evaluator pass/fail is stored as a `backtest_results` row so the full iteration history is visible.
- **Cron schedule:** None — all runs are triggered on-demand.
- **Authentication:** All endpoints (except `/health`) require `X-API-Key` header; key configured via `API_KEY` env var.
- **Code execution safety:** All backtesting code runs exclusively inside E2B sandboxes. One sandbox per research run; sandbox is closed after the run completes or fails.
- **RAG seeding:** A `seed.py` script pre-populates ChromaDB with default investor philosophy texts at service startup (if the collection is empty). Additional documents can be added via the `/documents` API.
- **E2B sandbox timeout:** Configurable via `E2B_TIMEOUT_SECONDS` env var (default: `60`).
