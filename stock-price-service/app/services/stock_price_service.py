from datetime import date

from sqlalchemy.orm import Session

from app.repositories.stock_price_repository import StockPriceRepository
from app.schemas.stock_price import StockPriceItem, StockPriceListResponse


class StockPriceService:
    def __init__(self, db: Session) -> None:
        self.repo = StockPriceRepository(db)

    def get_prices(
        self,
        ticker: str,
        start_date: date | None,
        end_date: date | None,
        offset: int,
        limit: int,
    ) -> StockPriceListResponse:
        items, total = self.repo.get_by_ticker(
            ticker.upper(), start_date, end_date, offset, limit
        )
        return StockPriceListResponse(
            ticker=ticker.upper(),
            total=total,
            offset=offset,
            limit=limit,
            items=[StockPriceItem.model_validate(item) for item in items],
        )
