# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See the root `CLAUDE.md` for monorepo-wide commands, shared architecture patterns, and infrastructure setup. This file covers what is specific to `stock-price-service`.

## Commands

Run from this directory (`stock-price-service/`):

```bash
uv sync                              # install dependencies
uv run alembic upgrade head          # run migrations
uv run uvicorn main:app --reload     # start API on :8000
uv run python cron.py                # run the price-fetch cron manually
uv run python worker.py              # start the SQS worker
uv run pytest tests/ -v              # run all tests
uv run pytest tests/test_fetch_service.py::test_name -v  # run a single test
```

Tests require no database — `conftest.py` sets a dummy `DATABASE_URL` env var and all tests use SQLite in-memory or mocks.

## Service-specific architecture

Three entry points:

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — mounts the `stock_prices` router |
| `cron.py` | Scheduled price fetcher — reads tickers, fetches via yfinance, upserts |
| `worker.py` | Long-polling SQS worker — handles `NEW_SYMBOL_ADDED` events |

### Services

- **`fetch_service.py`** — thin wrapper around yfinance; returns a list of OHLC dicts for a symbol and date range.
- **`cron_service.py`** — orchestrates the full fetch cycle: reads all tickers → calls `fetch_service` → upserts via `stock_price_repository.upsert_many` → updates `ticker.last_fetch_date`. Exits with code 1 if any ticker fails (for scheduler retry detection).
- **`stock_price_service.py`** — business logic for the API; delegates reads to `stock_price_repository`.

### SQS worker

`worker.py` polls `stock-price-new-symbol-queue` (a dedicated per-service queue, distinct from the shared `stock-events-queue`). SNS wraps the payload in an outer `Message` field — `process_message` double-decodes JSON to extract the inner `event` and `symbol`. The `handle_new_symbol_added` handler is a stub (TODO).

### Configuration (`.env`)

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | required | PostgreSQL connection string |
| `DEFAULT_START_DATE` | `2020-01-01` | Fetch start date when a ticker has no history |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | Override to point at real AWS |
| `SQS_NEW_SYMBOL_QUEUE_URL` | LocalStack default | Queue polled by `worker.py` |

### API

`GET /api/v1/stocks/{ticker}` — returns paginated OHLC history sorted by date descending.
Query params: `start_date`, `end_date` (inclusive, `YYYY-MM-DD`), `offset` (default 0), `limit` (default 50, max 500).

`GET /health` — liveness probe, returns `{"status": "ok"}`.

### Database tables

- **`tickers`** — `(id, symbol, last_fetch_date)` — managed externally; this service only reads and updates `last_fetch_date`.
- **`stock_prices`** — `(id, ticker, date, open, high, low, close)` — unique constraint on `(ticker, date)`; upserted with `DO UPDATE`.
