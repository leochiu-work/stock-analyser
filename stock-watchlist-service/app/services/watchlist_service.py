from sqlalchemy.orm import Session

from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import WatchlistResponse, WatchlistTickerItem


class WatchlistService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = WatchlistRepository()

    def get_all(self) -> WatchlistResponse:
        tickers = self._repo.get_all(self._db)
        items = [WatchlistTickerItem.model_validate(t) for t in tickers]
        return WatchlistResponse(total=len(items), items=items)

    def add_ticker(self, symbol: str) -> WatchlistTickerItem:
        ticker = self._repo.add(self._db, symbol)
        return WatchlistTickerItem.model_validate(ticker)

    def remove_ticker(self, symbol: str) -> bool:
        return self._repo.delete_by_symbol(self._db, symbol.strip().upper())
