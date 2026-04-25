# Stock Analyser

> **Academic Disclaimer:** This project is built for learning and academic purposes only. Nothing in this repository constitutes financial advice. Do not make investment decisions based on the output of this system.

A monorepo of Python microservices and a Next.js dashboard for fetching, storing, and analysing stock market data. The centrepiece is an AI-powered trading strategy research service that uses a local LLM (via Ollama) and a LangGraph multi-agent workflow to generate, backtest, and evaluate trading strategies.

---

## Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │               dashboard  :3000               │
                        └────────────────────┬────────────────────────┘
                                             │ REST
          ┌──────────────────────────────────┼──────────────────────────────────┐
          │                       │          │          │                        │
          ▼                       ▼          ▼          ▼                        ▼
  watchlist-service         news-service  price-service  ta-service    strategy-finder
      :8002                    :8003         :8004        :8005             :8006
          │                       │          │          │                        │
          │  SNS: new-symbol-added│          │          │                        │
          └────────────────────►  │          │          │                        │
                                  └──────────┘          │                        │
                                       │  SNS: prices-fetched                    │
                                       └───────────────►│                        │
                                                                                 │
                                              Ollama (local LLM)  ◄─────────────┤
                                              ChromaDB (vectors)  ◄─────────────┤
                                              E2B Sandbox         ◄─────────────┘

              PostgreSQL :5432          LocalStack (SNS/SQS) :4566
```

---

## Services

### stock-watchlist-service — port 8002

Manages the list of stock tickers you want to track. Adding a ticker publishes a `NEW_SYMBOL_ADDED` SNS event that triggers the price and news services to start fetching data automatically.

---

### stock-news-service — port 8003

Fetches company news articles from the [Finnhub](https://finnhub.io) API and stores them in PostgreSQL. A cron job incrementally fetches new articles for each tracked ticker; a worker process listens for `NEW_SYMBOL_ADDED` events to kick off the initial fetch for newly added symbols.

---

### stock-price-service — port 8004

Fetches historical OHLC (Open, High, Low, Close) price data from [yfinance](https://github.com/ranaroussi/yfinance) and stores it in PostgreSQL. Uses the same cron + worker pattern as the news service. After a successful price fetch it publishes a `PRICES_FETCHED` SNS event.

---

### stock-ta-service — port 8005

Computes technical analysis indicators from the stored OHLC data using the [`ta`](https://technical-analysis-library-in-python.readthedocs.io/) library. Subscribes to the `PRICES_FETCHED` SNS event so indicators are recalculated automatically whenever new prices arrive.

**Indicators computed:** SMA (20, 50, 200), EMA (12, 26), RSI (14), MACD (line/signal/histogram), Bollinger Bands (upper/middle/lower), ATR (14), Stochastic Oscillator (%K/%D)

---

### trading-strategy-finder — port 8006

An AI-powered research service that uses a **LangGraph multi-agent workflow** to generate and evaluate trading strategies. The pipeline runs fully locally — no external LLM API required.

Each `graph.invoke()` call runs the pipeline once and produces one strategy. The service layer calls the graph up to `max_iterations` times, carrying forward previous hypotheses and rejection reasons so each attempt learns from the last. All strategies are persisted; the loop stops early if one is approved.

```
researcher → fetcher → coder → executor → evaluator → END
                                   │ (code error, retry < 3)
                                 coder (retry)
```

| Node | Role |
|------|------|
| **Researcher** | RAG query against ChromaDB (investor philosophy documents) → generates a trading hypothesis via Ollama |
| **Fetcher** | Pulls OHLCV data from stock-price-service and TA indicators from stock-ta-service, produces a CSV |
| **Coder** | Generates `backtesting.py` strategy code; retries up to 3 times on execution errors |
| **Executor** | Runs the strategy in an isolated [E2B](https://e2b.dev) sandbox; captures backtest statistics |
| **Evaluator** | LLM scores the results with structured output (score, approved/rejected, reasoning); always ends the graph |

---

### dashboard — port 3000

A Next.js frontend that ties everything together. Provides pages for browsing prices, news, the watchlist, and AI-generated strategy results. All backend calls are proxied through Next.js API routes.

---

## Tech Stack

| Service | Stack |
|---------|-------|
| stock-watchlist-service | FastAPI, SQLAlchemy, Alembic, PostgreSQL, AWS SNS (LocalStack) |
| stock-news-service | FastAPI, SQLAlchemy, Alembic, PostgreSQL, AWS SNS/SQS (LocalStack), Finnhub API |
| stock-price-service | FastAPI, SQLAlchemy, Alembic, PostgreSQL, AWS SNS/SQS (LocalStack), yfinance |
| stock-ta-service | FastAPI, SQLAlchemy, Alembic, PostgreSQL, AWS SQS (LocalStack), ta library |
| trading-strategy-finder | FastAPI, SQLAlchemy, Alembic, PostgreSQL, LangGraph, Ollama, ChromaDB, E2B Sandbox |
| dashboard | Next.js, React |
| Infrastructure | PostgreSQL 17, LocalStack (SNS/SQS), ChromaDB, Docker Compose |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/) | All services run in containers |
| [Ollama](https://ollama.com) | Local LLM runtime for trading-strategy-finder |
| [Finnhub API key](https://finnhub.io) | Free tier is sufficient for stock-news-service |
| [E2B API key](https://e2b.dev) | Used by trading-strategy-finder to execute backtest code in a sandbox |

---

## Getting Started

### 1. Install Ollama and pull the required models

```bash
# Install Ollama — see https://ollama.com for platform-specific instructions
ollama pull gemma3            # LLM used for reasoning and evaluation
ollama pull nomic-embed-text  # Embedding model used for RAG
```

Ollama must be running (`ollama serve`) before starting the stack.

### 2. Copy and fill in environment files

Each service has a `.env.example` file. Copy it to `.env` and fill in your credentials:

```bash
cp stock-news-service/.env.example stock-news-service/.env
cp trading-strategy-finder/.env.example trading-strategy-finder/.env
# repeat for any other service you want to configure
```

Key variables:

| Service | Variable | Description |
|---------|----------|-------------|
| stock-news-service | `FINNHUB_API_KEY` | Your Finnhub API key |
| trading-strategy-finder | `E2B_API_KEY` | Your E2B sandbox API key |
| trading-strategy-finder | `OLLAMA_BASE_URL` | Ollama endpoint (default: `http://host.docker.internal:11434`) |
| trading-strategy-finder | `OLLAMA_MODEL` | LLM model name (default: `gemma3`) |
| trading-strategy-finder | `OLLAMA_EMBED_MODEL` | Embedding model (default: `nomic-embed-text`) |
| trading-strategy-finder | `STRATEGY_API_KEY` | API key required by the strategy service |
| dashboard | `STRATEGY_API_KEY` | Must match the value above |

### 3. Start the stack

```bash
docker compose up -d
```

This starts PostgreSQL, LocalStack (SNS/SQS), ChromaDB, all five Python microservices, and the Next.js dashboard.

### 4. Run database migrations

Each Python service manages its own schema with Alembic. Once the stack is up, run migrations for every service:

```bash
docker compose exec stock-price-service uv run alembic upgrade head
docker compose exec stock-news-service uv run alembic upgrade head
docker compose exec stock-watchlist-service uv run alembic upgrade head
docker compose exec stock-ta-service uv run alembic upgrade head
docker compose exec trading-strategy-finder uv run alembic upgrade head
```

Migrations are idempotent — safe to re-run. You will need to re-run them whenever a service adds a new migration file.

### 5. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000).

Add a ticker via the **Watchlist** page — the price and news services will start fetching data automatically, and the TA service will compute indicators once prices are available.

---

## TODO

- [ ] Use Dockerfile for all microservices to automatically run schema migrations on startup
- [ ] Add `stock-news-sentiment-service` — analyses news sentiment using an LLM and produces a score per article/ticker; feed sentiment scores into `trading-strategy-finder` as an additional input signal
- [ ] Add RAG to `trading-strategy-finder` — seed ChromaDB with famous trader/investor philosophies so the researcher node can ground hypotheses in established strategies
- [ ] Split `trading-strategy-finder` into two services: a dedicated `trading-strategy-service` for persistence/querying and a separate research/agent service
- [ ] Build an MCP server for the fetcher node so it can selectively fetch only the data relevant to the current hypothesis, rather than pulling all available indicators
- [ ] Add a social media monitoring service — track posts from influential figures (e.g. Donald Trump, Elon Musk) whose public statements can move stock prices; feed signals into the strategy pipeline
- [ ] Improve the coder node — switch to a more capable model and inject up-to-date `backtesting.py` library documentation into the prompt to reduce code errors
- [ ] Integrate IBKR (Interactive Brokers) sandbox to simulate real trade execution when a strategy is approved
