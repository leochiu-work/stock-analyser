import sys
import logging

from fastapi import FastAPI

from app.routers import news

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout  # Ensure it goes to the same stream as Uvicorn
)

app = FastAPI(
    title="Stock News Service",
    description="Provides company news articles fetched from Finnhub.",
    version="0.1.0",
)

app.include_router(news.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
