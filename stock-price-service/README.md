# stock-price-service

A microservice that fetches historical OHLC stock prices from [yfinance](https://github.com/ranaroussi/yfinance) and stores them in PostgreSQL. Exposes a REST API for querying price history.

## Features

- **Cron job** — fetches prices incrementally (from each ticker's last fetch date to today) and upserts into PostgreSQL. Designed to be triggered by an external scheduler such as a Kubernetes CronJob.
- **REST API** — query OHLC price history for any ticker with date filtering and pagination.
- **Idempotent** — re-running the cron job on the same day is safe; it upserts and skips tickers already up to date.

---

## Architecture

```
stock-price-service/
├── app/
│   ├── config.py                  # Settings via pydantic-settings (.env)
│   ├── database.py                # SQLAlchemy engine and session
│   ├── models/
│   │   ├── stock_price.py         # ORM model: stock_prices table
│   │   └── ticker.py              # ORM model: tickers table
│   ├── repositories/
│   │   ├── stock_price_repository.py  # DB operations for stock prices
│   │   └── ticker_repository.py       # DB operations for tickers
│   ├── services/
│   │   ├── fetch_service.py       # yfinance wrapper
│   │   ├── cron_service.py        # Orchestrates fetch → upsert → update
│   │   └── stock_price_service.py # Business logic for the API
│   ├── schemas/
│   │   └── stock_price.py         # Pydantic request/response models
│   └── routers/
│       └── stock_prices.py        # GET /api/v1/stocks/{ticker}
├── alembic/                       # Database migrations
├── tests/                         # Unit tests (fully mocked, no real DB)
├── main.py                        # FastAPI application entry point
├── cron.py                        # Cron job entry point
└── Dockerfile
```

### Database tables

**`tickers`** — source of truth for which symbols to track (managed externally).

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `symbol` | varchar(20) | Ticker symbol (e.g. `AAPL`) |
| `last_fetch_date` | date | Last date prices were successfully fetched; `NULL` if never fetched |

**`stock_prices`** — OHLC price history.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `ticker` | varchar(20) | Ticker symbol |
| `date` | date | Trading date |
| `open` | float | Opening price |
| `high` | float | Daily high |
| `low` | float | Daily low |
| `close` | float | Closing price (adjusted) |

Unique constraint on `(ticker, date)`.

---

## Configuration

Copy `.env.example` to `.env` and set the required values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `DEFAULT_START_DATE` | No | `2020-01-01` | Earliest date to fetch when a ticker has no prior history |

Example:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/stock_prices
DEFAULT_START_DATE=2020-01-01
```

> PostgreSQL is external to this service. The connection string can point to any reachable PostgreSQL instance.

---

## Getting started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A running PostgreSQL instance

### Install dependencies

```bash
uv sync
```

### Run database migrations

```bash
uv run alembic upgrade head
```

### Start the API server

```bash
uv run uvicorn main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run the cron job manually

```bash
uv run python cron.py
```

---

## API

### `GET /api/v1/stocks/{ticker}`

Returns paginated OHLC price history for a ticker, sorted by date descending.

**Path parameters**

| Parameter | Description |
|-----------|-------------|
| `ticker` | Ticker symbol (case-insensitive) |

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date (`YYYY-MM-DD`) | — | Filter from this date (inclusive) |
| `end_date` | date (`YYYY-MM-DD`) | — | Filter until this date (inclusive) |
| `offset` | integer ≥ 0 | `0` | Number of records to skip |
| `limit` | integer 1–500 | `50` | Max records to return |

**Example request**

```bash
curl "http://localhost:8000/api/v1/stocks/AAPL?start_date=2024-01-01&end_date=2024-03-31&limit=10"
```

**Example response**

```json
{
  "ticker": "AAPL",
  "total": 62,
  "offset": 0,
  "limit": 10,
  "items": [
    {
      "ticker": "AAPL",
      "date": "2024-03-28",
      "open": 171.03,
      "high": 171.86,
      "low": 170.01,
      "close": 171.48
    }
  ]
}
```

### `GET /health`

Returns `{"status": "ok"}`. Used for liveness probes.

---

## Cron job

`cron.py` is the entry point for the scheduled price fetcher. It is designed to be invoked by an external scheduler (e.g. Kubernetes CronJob — see `k8s/stock-price-service/`).

**Fetch logic per ticker:**

1. Read `last_fetch_date` from the `tickers` table.
2. If `last_fetch_date` is `NULL`, fetch from `DEFAULT_START_DATE` to today.
3. If `last_fetch_date` is today or in the future, skip.
4. Otherwise, fetch from `last_fetch_date + 1 day` to today.
5. Upsert results into `stock_prices`.
6. Update `last_fetch_date` to today.

If a ticker fails, it is logged and skipped — other tickers continue processing. The process exits with code `1` if any ticker failed, so the scheduler can detect and retry.

> Tickers are read-only from this service's perspective. Add or remove symbols via the ticker management service.

---

## Development

### Run tests

```bash
uv run pytest tests/ -v
```

All 46 tests are fully unit-tested with mocked dependencies — no database connection required.

### Local database (Docker)

A `docker-compose.yaml` at the repository root starts a local PostgreSQL instance:

```bash
# From the repo root
docker compose up -d
```

Default credentials: host `localhost:5432`, database `stock_prices`, user/password `stock`.

### Docker

Build the image:

```bash
docker build -t stock-price-service .
```

Run the API server:

```bash
docker run --env-file .env -p 8000:8000 stock-price-service
```

Run the cron job:

```bash
docker run --env-file .env stock-price-service uv run python cron.py
```
