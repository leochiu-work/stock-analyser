# stock-ta-service — Requirements

## Overview

`stock-ta-service` computes technical analysis (TA) indicators from OHLC price data and exposes the results via a REST API. It is triggered by `stock-price-service` via an SNS/SQS event after new prices are fetched. For each ticker event received, it retrieves the full OHLC history from `stock-price-service`, computes a broad set of indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic), and upserts the per-day results into its own PostgreSQL database.

## Consumers & Dependencies

| Direction | Service / Client      | Notes                                                                                      |
| --------- | --------------------- | ------------------------------------------------------------------------------------------ |
| Inbound   | `stock-price-service` | Publishes `PRICES_FETCHED` event to `prices-fetched` SNS topic after each successful fetch |
| Inbound   | `dashboard`           | Queries TA indicators via REST API for display                                             |
| Outbound  | `stock-price-service` | HTTP `GET /api/v1/stocks/{ticker}` to retrieve OHLC history for computation                |

## Tech Stack

| Layer       | Choice            | Notes                                                |
| ----------- | ----------------- | ---------------------------------------------------- |
| Language    | Python 3.12       |                                                      |
| Framework   | FastAPI           | Matches all existing services                        |
| Database    | PostgreSQL        | Database name: `stock_ta`                            |
| ORM         | SQLAlchemy        | Alembic for migrations                               |
| Settings    | pydantic-settings | Reads from `.env`                                    |
| TA library  | pandas-ta         | Pure-Python TA library built on pandas               |
| HTTP client | httpx             | Async-capable; fetches OHLC from stock-price-service |
| AWS         | boto3             | SQS long-polling worker                              |

## Database Schema

### `tickers`

| Column     | Type        | Notes            |
| ---------- | ----------- | ---------------- |
| id         | INTEGER PK  | Auto-increment   |
| symbol     | VARCHAR(16) | Unique, not null |
| created_at | TIMESTAMP   | Default now()    |

### `ta_indicators`

| Column      | Type        | Notes                                                          |
| ----------- | ----------- | -------------------------------------------------------------- |
| id          | INTEGER PK  | Auto-increment                                                 |
| ticker      | VARCHAR(16) | Not null; FK to tickers.symbol                                 |
| date        | DATE        | Not null                                                       |
| sma_20      | FLOAT       | Simple Moving Average 20-period; nullable if insufficient data |
| sma_50      | FLOAT       | Simple Moving Average 50-period; nullable                      |
| sma_200     | FLOAT       | Simple Moving Average 200-period; nullable                     |
| ema_12      | FLOAT       | Exponential Moving Average 12-period; nullable                 |
| ema_26      | FLOAT       | Exponential Moving Average 26-period; nullable                 |
| rsi_14      | FLOAT       | Relative Strength Index 14-period; nullable                    |
| macd_line   | FLOAT       | MACD line (EMA12 − EMA26); nullable                            |
| macd_signal | FLOAT       | MACD signal line (EMA9 of MACD); nullable                      |
| macd_hist   | FLOAT       | MACD histogram; nullable                                       |
| bb_upper    | FLOAT       | Bollinger Band upper (20-period, 2σ); nullable                 |
| bb_middle   | FLOAT       | Bollinger Band middle (SMA20); nullable                        |
| bb_lower    | FLOAT       | Bollinger Band lower; nullable                                 |
| atr_14      | FLOAT       | Average True Range 14-period; nullable                         |
| stoch_k     | FLOAT       | Stochastic %K; nullable                                        |
| stoch_d     | FLOAT       | Stochastic %D; nullable                                        |
| created_at  | TIMESTAMP   | Default now()                                                  |
| updated_at  | TIMESTAMP   | Updated on upsert                                              |

Unique constraint on `(ticker, date)`.

## API Endpoints

| Method | Path                         | Description                                                                      | Auth required |
| ------ | ---------------------------- | -------------------------------------------------------------------------------- | ------------- |
| GET    | `/api/v1/ta/{ticker}`        | TA indicators for a ticker; supports `start_date`, `end_date`, `limit`, `offset` | No            |
| GET    | `/api/v1/ta/{ticker}/latest` | Most recent TA row for a ticker                                                  | No            |
| GET    | `/health`                    | Liveness probe — returns `{"status": "ok"}`                                      | No            |

## External Integrations

| API / Service         | Auth method | Notes                                                                   |
| --------------------- | ----------- | ----------------------------------------------------------------------- |
| `stock-price-service` | None        | Internal HTTP; base URL configured via `PRICE_SERVICE_BASE_URL` env var |

## Message Queue Events

| Direction | Topic / Queue                | Event name       | Payload summary                                       |
| --------- | ---------------------------- | ---------------- | ----------------------------------------------------- |
| Subscribe | `prices-fetched` SNS topic   | `PRICES_FETCHED` | `{"event": "PRICES_FETCHED", "symbol": "AAPL"}`       |
| Subscribe | `stock-ta-service-queue` SQS | `PRICES_FETCHED` | Dedicated per-service queue subscribed to above topic |

## Non-Functional Requirements

- **Host port:** 8005
- **Internal port:** 8000 (inside container, matching all other services)
- **Idempotency:** `ta_indicators` upserts on `(ticker, date)` with `DO UPDATE` — safe to reprocess the same event
- **Cron schedule:** None — worker-triggered only
- **Authentication:** No caller authentication required (internal service)
- **Minimum history:** SMA-200 requires at least 200 trading days of OHLC; service always fetches full history and allows NaN for early rows
- **Rate limiting:** Inherits any rate limits from `stock-price-service` API; no additional caching required initially
