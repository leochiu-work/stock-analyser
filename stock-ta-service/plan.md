# stock-ta-service — Implementation Plan

## Directory Structure

```
stock-ta-service/
  main.py                          ← FastAPI app entry point
  worker.py                        ← SQS long-polling worker (PRICES_FETCHED handler)
  app/
    config.py                      ← pydantic-settings; reads from .env
    database.py                    ← SQLAlchemy engine, SessionLocal, get_db dependency
    models/
      __init__.py                  ← imports all models so Alembic sees metadata
      ticker.py                    ← Ticker ORM model
      ta_indicator.py              ← TAIndicator ORM model
    repositories/
      ticker_repository.py         ← get_or_create, get_all
      ta_repository.py             ← get_by_ticker, get_latest, upsert_many
    services/
      price_client.py              ← httpx client — fetches OHLC from stock-price-service
      ta_service.py                ← orchestrates fetch → compute → upsert
      ta_calculator.py             ← pure pandas-ta computation, returns list of dicts
    schemas/
      ta_indicator.py              ← TAIndicatorResponse, TAIndicatorListResponse
    routers/
      ta_router.py                 ← GET /api/v1/ta/{ticker} and /latest
  alembic/
    env.py                         ← imports app.models; reads DATABASE_URL from settings
    versions/                      ← migration files
  tests/
    conftest.py                    ← SQLite in-memory engine, override get_db
    test_ta_router.py
    test_ta_repository.py
    test_ta_calculator.py
    test_ta_service.py
  Dockerfile
  pyproject.toml
  .env.example
```

## Implementation Steps

1. **Scaffold project**
   - `uv init stock-ta-service` inside the repo root
   - Add dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `psycopg2-binary`, `pydantic-settings`, `pandas-ta`, `httpx`, `boto3`
   - Add dev dependencies: `pytest`, `pytest-asyncio`, `httpx` (test client), `pytest-mock`

2. **Config & environment** (`app/config.py`, `.env.example`)
   - Fields: `DATABASE_URL`, `PRICE_SERVICE_BASE_URL`, `AWS_ENDPOINT_URL`, `AWS_REGION`, `SQS_PRICES_FETCHED_QUEUE_URL`
   - `.env.example`:
     ```
     DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_ta
     PRICE_SERVICE_BASE_URL=http://stock-price-service:8000
     AWS_ENDPOINT_URL=http://localstack:4566
     AWS_REGION=us-east-1
     SQS_PRICES_FETCHED_QUEUE_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/stock-ta-prices-fetched-queue
     ```

3. **Database setup**
   - `app/database.py` — standard SQLAlchemy engine + `SessionLocal` + `get_db` dependency (identical pattern to existing services)
   - `app/models/ticker.py` — `Ticker(id, symbol, created_at)`
   - `app/models/ta_indicator.py` — `TAIndicator` with all columns from schema; UniqueConstraint on `(ticker, date)`
   - `alembic/env.py` — import `app.models` to register metadata; read `DATABASE_URL` from settings
   - Run `uv run alembic revision --autogenerate -m "create tickers and ta_indicators tables"`

4. **Repository layer** (`app/repositories/`)
   - `ticker_repository.py`:
     - `get_or_create(db, symbol) -> Ticker`
     - `get_all(db) -> list[Ticker]`
   - `ta_repository.py`:
     - `get_by_ticker(db, ticker, start_date, end_date, offset, limit) -> list[TAIndicator]`
     - `get_latest(db, ticker) -> TAIndicator | None`
     - `upsert_many(db, records: list[dict]) -> int` — PostgreSQL `INSERT ... ON CONFLICT (ticker, date) DO UPDATE`

5. **Service layer** (`app/services/`)
   - `price_client.py`:
     - `fetch_ohlc(symbol: str, limit: int = 1000) -> list[dict]`
     - Calls `GET {PRICE_SERVICE_BASE_URL}/api/v1/stocks/{symbol}?limit=1000` (paginate if needed to get full history)
   - `ta_calculator.py`:
     - `compute(symbol: str, ohlc_records: list[dict]) -> list[dict]`
     - Converts to pandas DataFrame; runs `pandas_ta` strategy for all indicators
     - Returns list of per-row dicts with `ticker`, `date`, and all indicator columns (NaN → None)
   - `ta_service.py`:
     - `compute_and_store(db, symbol: str) -> int`
     - Calls `price_client.fetch_ohlc` → `ta_calculator.compute` → `ta_repository.upsert_many`
     - Creates ticker row via `ticker_repository.get_or_create`

6. **Router / handlers** (`app/routers/ta_router.py`, `main.py`)
   - `GET /api/v1/ta/{ticker}` — query params: `start_date`, `end_date` (YYYY-MM-DD), `offset=0`, `limit=50` (max 500)
   - `GET /api/v1/ta/{ticker}/latest` — returns single most-recent row or 404
   - `main.py` mounts the router and adds `GET /health`

7. **SQS worker** (`worker.py`)
   - Matches `stock-price-service/worker.py` pattern exactly
   - Polls `SQS_PRICES_FETCHED_QUEUE_URL` with 20-second long-polling
   - Decodes SNS-wrapped JSON: `outer["Body"] → outer["Message"] → payload`
   - On `PRICES_FETCHED`: calls `ta_service.compute_and_store(db, payload["symbol"])`
   - Deletes message after successful processing; logs and skips on error

8. **LocalStack infrastructure** (`localstack/init/01_setup.sh`)
   - Add after existing setup:
     ```bash
     echo "Creating SNS topic: prices-fetched"
     PRICES_TOPIC_ARN=$(awslocal sns create-topic --name prices-fetched --query TopicArn --output text)

     echo "Creating SQS queue: stock-ta-prices-fetched-queue"
     TA_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-ta-prices-fetched-queue --query QueueUrl --output text)
     TA_QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url "$TA_QUEUE_URL" --attribute-names QueueArn --query Attributes.QueueArn --output text)

     awslocal sns subscribe --topic-arn "$PRICES_TOPIC_ARN" --protocol sqs --notification-endpoint "$TA_QUEUE_ARN"
     ```
   - `stock-price-service` must also be updated to publish `PRICES_FETCHED` events to `prices-fetched` SNS topic after each successful cron/worker fetch

9. **stock-price-service changes** (separate task)
   - Add `SNS_PRICES_FETCHED_TOPIC_ARN` to config and `.env.example`
   - In `cron_service.py`: after a successful `upsert_many`, publish `{"event": "PRICES_FETCHED", "symbol": symbol}` to the topic
   - In `worker.py` `handle_new_symbol_added`: same publish after successful fetch

10. **Tests** (`tests/`)
    - `conftest.py` — SQLite in-memory with `StaticPool`; override `get_db` and `settings`
    - `test_ta_calculator.py` — unit test with synthetic OHLC DataFrame; assert indicator columns present
    - `test_ta_repository.py` — insert rows via ORM, assert `get_by_ticker` / `get_latest` / `upsert_many` (mock the PG-specific upsert in unit tests)
    - `test_ta_router.py` — use `TestClient`; mock `ta_service`
    - `test_ta_service.py` — mock `price_client` and `ta_repository`; assert orchestration logic

11. **Dockerfile**
    ```dockerfile
    FROM python:3.12-slim
    WORKDIR /app
    COPY pyproject.toml uv.lock ./
    RUN pip install uv && uv sync --frozen --no-dev
    COPY . .
    EXPOSE 8000
    CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

12. **docker-compose** (root `docker-compose.yaml`)
    ```yaml
    stock-ta-service:
      build: ./stock-ta-service
      ports:
        - "8005:8000"
      env_file: ./stock-ta-service/.env
      depends_on:
        - postgres
        - localstack

    stock-ta-worker:
      build: ./stock-ta-service
      command: uv run python worker.py
      env_file: ./stock-ta-service/.env
      depends_on:
        - postgres
        - localstack
    ```

13. **PostgreSQL init** (`postgres/init.sql`)
    - Add: `CREATE DATABASE stock_ta;`

## Migration Plan

```bash
cd stock-ta-service
uv run alembic revision --autogenerate -m "create tickers and ta_indicators tables"
uv run alembic upgrade head
```

The first migration creates both `tickers` and `ta_indicators` with the unique constraint on `(ticker, date)`.

## Testing Approach

- SQLite in-memory with `StaticPool` for all DB-touching tests
- `ta_calculator.py` is pure pandas logic — tested in isolation with a synthetic 300-row OHLC DataFrame
- External HTTP calls (`price_client`) mocked with `pytest-mock`
- `upsert_many` uses `sqlalchemy.dialects.postgresql.insert` — mocked in unit tests; tested at integration level against a real DB if needed
- Run all tests: `uv run pytest tests/ -v`

## Open Questions

- **Pagination in price_client**: `stock-price-service` defaults to `limit=50` max 500. For tickers with > 500 days of history, `price_client` must paginate. Confirm max records needed (SMA-200 requires ~200 days minimum; full 5-year history = ~1250 rows).
- **SNS topic naming**: Confirm `prices-fetched` topic name with team before updating `localstack/init/01_setup.sh`.
- **Dashboard integration**: Determine which TA indicators and time ranges the dashboard will need to display — may influence default `limit` for `GET /api/v1/ta/{ticker}`.
- **pandas-ta vs ta-lib**: `pandas-ta` is pure Python and easy to install in Docker. If performance becomes an issue with large datasets, consider `ta-lib` (requires C bindings in Dockerfile).
