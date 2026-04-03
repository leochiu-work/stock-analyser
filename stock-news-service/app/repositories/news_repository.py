from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.news import News


class NewsRepository:
    def upsert_many(self, db: Session, records: list[dict]) -> int:
        """Insert news records, ignoring duplicates by finnhub_id. Returns count inserted."""
        if not records:
            return 0
        stmt = insert(News).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["finnhub_id"])
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    def get_by_ticker(
        self,
        db: Session,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[News], int]:
        """Return paginated news for a ticker, sorted by published_at descending."""
        query = db.query(News).filter(News.ticker_symbol == ticker)
        if start_date:
            query = query.filter(News.published_at >= start_date)
        if end_date:
            query = query.filter(News.published_at <= end_date)
        total = query.count()
        items = (
            query.order_by(News.published_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total
