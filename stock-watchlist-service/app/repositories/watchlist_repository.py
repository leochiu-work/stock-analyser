from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistTicker


class WatchlistRepository:
    def get_all(self, db: Session) -> list[WatchlistTicker]:
        return db.query(WatchlistTicker).order_by(WatchlistTicker.created_at).all()

    def add(self, db: Session, symbol: str) -> WatchlistTicker:
        stmt = insert(WatchlistTicker).values(symbol=symbol).on_conflict_do_nothing(
            index_elements=["symbol"]
        )
        db.execute(stmt)
        db.commit()
        return db.query(WatchlistTicker).filter(WatchlistTicker.symbol == symbol).one()
