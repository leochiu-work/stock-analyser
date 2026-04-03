from fastapi import FastAPI

from app.routers import news

app = FastAPI(
    title="Stock News Service",
    description="Provides company news articles fetched from Finnhub.",
    version="0.1.0",
)

app.include_router(news.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
