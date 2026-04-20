import sys
import logging

from fastapi import FastAPI

from app.routers import stock_prices


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout  # Ensure it goes to the same stream as Uvicorn
)

app = FastAPI(
    title="Stock Price Service",
    description="Provides historical OHLC stock prices.",
    version="0.1.0",
)

app.include_router(stock_prices.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
