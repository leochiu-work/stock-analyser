from fastapi import FastAPI

from app.routers import stock_prices

app = FastAPI(
    title="Stock Price Service",
    description="Provides historical OHLC stock prices.",
    version="0.1.0",
)

app.include_router(stock_prices.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
