from datetime import date

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.stock_price import StockPrice


class StockPriceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, records: list[dict]) -> int:
        """Insert or update stock price records. Returns number of rows affected."""
        if not records:
            return 0
        stmt = insert(StockPrice).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_stock_price_ticker_date",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
            },
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def get_by_ticker(
        self,
        ticker: str,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockPrice], int]:
        """Return paginated stock prices for a ticker, sorted by date descending."""
        query = self.db.query(StockPrice).filter(StockPrice.ticker == ticker)
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        total = query.count()
        items = (
            query.order_by(StockPrice.date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total
