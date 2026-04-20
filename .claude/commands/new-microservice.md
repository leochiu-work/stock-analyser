---
name: new-microservice
description: Draft requirements and an implementation plan for a new microservice. Invoked when the user asks to "create a new microservice", "add a new service", or "design a new service". Gathers details interactively, then writes requirement.md and plan.md into the new service directory.
argument-hint: [service-name]
allowed-tools: AskUserQuestion, Write, Read, Glob
---

You are helping the user design a new microservice from scratch. Your job is to gather all the details needed, then produce two files: `requirement.md` and `plan.md` inside the new service's directory.

Follow these steps **in order**. Do not skip steps or bundle all questions into one.

---

## Step 1 — Identity & Purpose

Use AskUserQuestion to ask:

> **Let's design your new microservice. First, some basics:**
>
> 1. **Service name** — what will the directory be called? (e.g. `stock-alert-service`)
> 2. **Purpose** — what is this service responsible for? What problem does it solve?
> 3. **Consumers** — which other services or clients will call this service? Which services will this service call?

Record the answers. The service name determines the output directory path (`<repo-root>/<service-name>/`).

---

## Step 2 — Tech Stack

Use AskUserQuestion to ask:

> **Now for the technology choices:**
>
> 1. **Programming language** — Python, Node.js, Go, or other?
> 2. **API framework** — e.g. FastAPI, Express, Gin, Spring Boot. (Or "none" if this is a worker with no HTTP API.)
> 3. **Key libraries / dependencies** — any specific packages you already know you need? (e.g. `yfinance`, `httpx`, `boto3`, Prisma, etc.)

Record the answers.

---

## Step 3 — Data & Persistence

Use AskUserQuestion to ask:

> **Data storage:**
>
> 1. **Database engine** — PostgreSQL, MySQL, MongoDB, Redis, SQLite, or none?
> 2. **Key entities / tables** — briefly describe the main data you need to store. (e.g. "a `prices` table with ticker, date, open, close, volume")
> 3. **Cron / background job** — does this service need a scheduled job that runs periodically? If yes, what does it do and how often?

Record the answers.

---

## Step 4 — Integration & Infrastructure

Use AskUserQuestion to ask:

> **Integrations and infrastructure:**
>
> 1. **External APIs** — which third-party APIs does this service consume? How are they authenticated? (API key, OAuth, etc.)
> 2. **Message queue** — does this service publish or subscribe to any SNS/SQS topics or queues? Which events?
> 3. **Host port** — what port should this service expose on the host? (existing services use 8002–8004)
> 4. **Authentication** — does the API itself require any authentication from callers?
> 5. **Any other requirements** — rate limits, caching, special compliance needs, etc.?

Record the answers.

---

## Step 5 — Confirm & Generate

Briefly summarise the collected information back to the user in a short table, then say you are about to create the two files. Do NOT ask for approval — just proceed.

---

## Step 6 — Create `requirement.md`

Write `<service-name>/requirement.md` with this structure:

```
# <Service Name> — Requirements

## Overview
<One paragraph description of the service's purpose and responsibilities.>

## Consumers & Dependencies
| Direction | Service / Client | Notes |
|-----------|-----------------|-------|
| Inbound   | ...             | ...   |
| Outbound  | ...             | ...   |

## Tech Stack
| Layer       | Choice           | Notes |
|-------------|-----------------|-------|
| Language    | ...             |       |
| Framework   | ...             |       |
| Database    | ...             |       |
| Key libs    | ...             |       |

## Database Schema
### `<table_name>`
| Column | Type | Notes |
|--------|------|-------|
| ...    | ...  | ...   |

(Repeat for each table.)

## API Endpoints
| Method | Path | Description | Auth required |
|--------|------|-------------|---------------|
| GET    | /... | ...         | No            |

## External Integrations
| API / Service | Auth method | Notes |
|--------------|------------|-------|

## Message Queue Events
| Direction | Topic / Queue | Event name | Payload summary |
|-----------|--------------|-----------|-----------------|

## Non-Functional Requirements
- **Host port:** <port>
- **Idempotency:** <how upserts / retries are handled>
- **Cron schedule:** <if applicable>
- **Authentication:** <caller auth requirements>
- **Other:** <anything else noted>
```

---

## Step 7 — Create `plan.md`

Write `<service-name>/plan.md` with this structure. Mirror the conventions of the existing Python services unless the user chose a different language.

```
# <Service Name> — Implementation Plan

## Directory Structure
\`\`\`
<service-name>/
  main.py / index.ts / main.go   ← HTTP entry point
  cron.py                        ← scheduled job (if needed)
  app/
    config.py                    ← env-var settings (pydantic-settings or dotenv)
    database.py                  ← DB engine, session factory, get_db dependency
    models/                      ← ORM models
    repositories/                ← stateless DB query functions
    services/                    ← business logic, external API calls
    schemas/                     ← request/response Pydantic/Zod/Go structs
    routers/                     ← HTTP route handlers
  alembic/                       ← migrations (Python/PostgreSQL only)
  tests/
  Dockerfile
  pyproject.toml / package.json / go.mod
  .env.example
\`\`\`

## Implementation Steps

1. **Scaffold project** — create directory, init package manager, add dependencies.
2. **Config & environment** — define settings class / config loader; create `.env.example`.
3. **Database setup** — define ORM models; write initial Alembic migration (or equivalent).
4. **Repository layer** — implement stateless query functions (get, upsert, delete).
5. **Service layer** — implement business logic; integrate external API client.
6. **Router / handlers** — implement HTTP endpoints; wire up Depends(get_db).
7. **Cron job** (if needed) — implement scheduler using `cron.py` or a worker entrypoint.
8. **Message queue** (if needed) — implement SNS publish / SQS consumer logic.
9. **Tests** — write unit tests with SQLite in-memory DB; mock external APIs.
10. **Dockerfile** — write multi-stage Dockerfile; expose port 8000 internally.
11. **docker-compose** — add service block to root `docker-compose.yaml`; set host port.
12. **PostgreSQL init** (if new DB) — add `CREATE DATABASE` to `postgres/init.sql`.

## Migration Plan
- Use Alembic (`uv run alembic revision --autogenerate -m "<description>"`)
- Run with `uv run alembic upgrade head`
- First migration creates all tables defined in the schema

## Docker / docker-compose Addition
\`\`\`yaml
<service-name>:
  build: ./<service-name>
  ports:
    - "<host-port>:8000"
  env_file: ./<service-name>/.env
  depends_on:
    - postgres
\`\`\`

## Testing Approach
- SQLite in-memory with StaticPool for all DB tests
- Mock external HTTP calls with `unittest.mock` / `pytest-mock` / `msw`
- `uv run pytest tests/ -v` (Python) or `npm test` (Node)
- PostgreSQL-specific upsert logic tested at integration level or mocked in unit tests

## Open Questions
<List any unresolved decisions, e.g. "confirm SNS topic name with infra team".>
```

---

After writing both files, tell the user where the files were created and suggest the next step (e.g. "run `/new-microservice` again or start scaffolding with `uv init`").
