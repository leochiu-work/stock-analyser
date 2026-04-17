# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

A monorepo of Python microservices and a Next.js dashboard that fetch and serve financial data. Each Python service is fully independent — own dependencies, database, and Dockerfile.

| Service | Host Port | Data Source | Database |
|---------|-----------|-------------|----------|
| `stock-price-service` | 8004 | yfinance (OHLC prices) | `stock_price` |
| `stock-news-service` | 8003 | Finnhub (news articles) | `stock_news` |
| `stock-watchlist-service` | 8002 | — (local only) | `stock_watchlist` |
| `dashboard` | 3000 | Proxies to above services | — |

All Python services listen on port 8000 inside their container; host ports differ as above.

## Common Commands

### Python services

All commands run from within the service directory (e.g. `cd stock-price-service`).

```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the API server (with hot reload)
uv run uvicorn main:app --reload

# Run the cron job manually (stock-price-service and stock-news-service only)
uv run python cron.py

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_news_router.py -v

# Run a single test by name
uv run pytest tests/test_news_router.py::test_get_news_start_date_filter -v
```

### Dashboard (Next.js)

```bash
cd dashboard
npm install
npm run dev   # starts on :3000
```

## Local Infrastructure

All services, PostgreSQL, and LocalStack are defined at the repo root:

```bash
docker compose up -d   # starts all services, postgres on :5432, localstack on :4566
```

PostgreSQL is initialised with three databases by `postgres/init.sql`:
- `stock_price`, `stock_news`, `stock_watchlist`

LocalStack (`localstack/init/01_setup.sh`) creates:
- SNS topic: `stock-events`
- SQS queue: `stock-events-queue` (subscribed to the topic)

Each Python service has a `.env.example` — copy to `.env` and fill in credentials before running locally.

## Architecture

### Python microservices

All three services follow an identical layered pattern:

```
main.py / cron.py           ← entry points
app/
  config.py                 ← pydantic-settings reads from .env
  database.py               ← SQLAlchemy engine, SessionLocal, get_db dependency
  models/                   ← SQLAlchemy ORM models (registered in models/__init__.py for Alembic)
  repositories/             ← all DB queries; stateless — db: Session passed as first arg
  services/                 ← business logic; orchestrates repos and external APIs
  schemas/                  ← Pydantic request/response models (model_config from_attributes=True)
  routers/                  ← FastAPI route handlers; use Depends(get_db)
alembic/
  env.py                    ← imports app.models to register metadata; reads URL from settings
  versions/                 ← one migration file per schema version
```

### Dashboard (Next.js BFF)

```
dashboard/src/app/
  api/prices/route.ts       ← proxies to stock-price-service
  api/news/route.ts         ← proxies to stock-news-service
  prices/page.tsx
  news/page.tsx
```

Upstream URLs are injected via environment variables (`PRICE_API_BASE_URL`, `NEWS_API_BASE_URL`, `WATCHLIST_API_BASE_URL`).

### Key design decisions

- **Tickers table is the fetch source of truth.** The cron job reads all rows from `tickers` and fetches data for each. Add a symbol to `tickers` to start tracking it; the cron handles the rest.
- **`last_fetch_date` drives incremental fetching.** If `NULL`, the cron fetches from a default start date (stock-price) or the last 30 days (stock-news). After a successful fetch, it is updated to today.
- **Upsert for idempotency.** `upsert_many` uses PostgreSQL `INSERT ... ON CONFLICT` so re-running the cron on the same day is safe. stock-price uses `DO UPDATE`; stock-news uses `DO NOTHING` (keyed on `finnhub_id`).
- **Repositories are stateless.** They never store `db` — the session is passed into every method. This makes them trivial to test with a mock session.
- **Services convert date boundaries.** The `news_service` converts `date` query params to `datetime` bounds (`time.min` / `time.max`) before passing to the repository so end-of-day inclusive filtering works correctly against the `DateTime` column.
- **Tests use SQLite in-memory** with `StaticPool` (single shared connection) so all threads/fixtures see the same database without a real PostgreSQL instance.
- **PostgreSQL-specific upserts are not tested directly.** `upsert_many` uses `sqlalchemy.dialects.postgresql.insert` which is incompatible with SQLite. Tests insert data via the ORM directly and mock `upsert_many` where needed.
