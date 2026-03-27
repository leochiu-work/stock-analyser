from datetime import date

from pydantic import BaseModel, ConfigDict


class StockPriceItem(BaseModel):
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float

    model_config = ConfigDict(from_attributes=True)


class StockPriceListResponse(BaseModel):
    ticker: str
    total: int
    offset: int
    limit: int
    items: list[StockPriceItem]
