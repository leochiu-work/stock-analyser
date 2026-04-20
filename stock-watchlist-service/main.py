import sys
import logging

from fastapi import FastAPI

from app.routers import watchlist



logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout  # Ensure it goes to the same stream as Uvicorn
)

app = FastAPI(
    title="Stock Watchlist Service",
    description="Manages a watchlist of stock ticker symbols.",
    version="0.1.0",
)

app.include_router(watchlist.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
