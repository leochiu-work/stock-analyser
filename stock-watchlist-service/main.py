from fastapi import FastAPI

from app.routers import watchlist

app = FastAPI(
    title="Stock Watchlist Service",
    description="Manages a watchlist of stock ticker symbols.",
    version="0.1.0",
)

app.include_router(watchlist.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
