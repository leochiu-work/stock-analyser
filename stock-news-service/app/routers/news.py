from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.news_repository import NewsRepository
from app.schemas.news import NewsListResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("/{ticker}", response_model=NewsListResponse)
def get_ticker_news(
    ticker: str,
    start_date: Annotated[date | None, Query(description="Filter from this date (inclusive)")] = None,
    end_date: Annotated[date | None, Query(description="Filter until this date (inclusive)")] = None,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=500, description="Max records to return")] = 50,
    db: Session = Depends(get_db),
) -> NewsListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    news_repo = NewsRepository()
    service = NewsService(db, news_repo)
    return service.get_news(ticker, start_date, end_date, offset, limit)
