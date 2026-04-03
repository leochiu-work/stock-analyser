from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.repositories.news_repository import NewsRepository
from app.schemas.news import NewsItem, NewsListResponse


class NewsService:
    def __init__(self, db: Session, news_repo: NewsRepository) -> None:
        self.db = db
        self.news_repo = news_repo

    def get_news(
        self,
        ticker: str,
        start_date: date | None,
        end_date: date | None,
        offset: int,
        limit: int,
    ) -> NewsListResponse:
        # Convert date boundaries to datetime for inclusive comparison against
        # the datetime-typed published_at column.
        start_dt = datetime.combine(start_date, time.min) if start_date else None
        end_dt = datetime.combine(end_date, time.max) if end_date else None
        items, total = self.news_repo.get_by_ticker(
            self.db, ticker.upper(), start_dt, end_dt, offset, limit
        )
        return NewsListResponse(
            total=total,
            offset=offset,
            limit=limit,
            items=[NewsItem.model_validate(item) for item in items],
        )
