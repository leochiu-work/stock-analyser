from datetime import date

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.ta_indicator import TAIndicator


class TARepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_ticker(
        self,
        ticker: str,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[TAIndicator]:
        query = self.db.query(TAIndicator).filter(TAIndicator.ticker == ticker)
        if start_date:
            query = query.filter(TAIndicator.date >= start_date)
        if end_date:
            query = query.filter(TAIndicator.date <= end_date)
        return query.order_by(TAIndicator.date.desc()).offset(offset).limit(limit).all()

    def get_latest(self, ticker: str) -> TAIndicator | None:
        return (
            self.db.query(TAIndicator)
            .filter(TAIndicator.ticker == ticker)
            .order_by(TAIndicator.date.desc())
            .first()
        )

    def upsert_many(self, records: list[dict]) -> int:
        if not records:
            return 0
        stmt = insert(TAIndicator).values(records)
        update_cols = {
            col: stmt.excluded[col]
            for col in [
                "sma_20", "sma_50", "sma_200",
                "ema_12", "ema_26",
                "rsi_14",
                "macd_line", "macd_signal", "macd_hist",
                "bb_upper", "bb_middle", "bb_lower",
                "atr_14",
                "stoch_k", "stoch_d",
                "updated_at",
            ]
        }
        stmt = stmt.on_conflict_do_update(
            constraint="uq_ta_ticker_date",
            set_=update_cols,
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
