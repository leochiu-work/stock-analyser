import asyncio
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import health, strategies, documents
import seed

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(seed.seed_if_empty)
    yield


app = FastAPI(
    title="Trading Strategy Finder",
    description="AI-powered trading strategy research service.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    api_key = request.headers.get("X-API-Key")
    if api_key != settings.api_key:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


app.include_router(health.router)
app.include_router(strategies.router)
app.include_router(documents.router)
