import sys
import logging

from fastapi import FastAPI

from app.routers import ta_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title="Stock TA Service",
    description="Computes technical analysis indicators from OHLC price data.",
    version="0.1.0",
)

app.include_router(ta_router.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
