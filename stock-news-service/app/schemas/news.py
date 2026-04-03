from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class NewsItem(BaseModel):
    ticker_symbol: str
    finnhub_id: int
    headline: str
    summary: str | None
    source: str | None
    url: str | None
    image: str | None
    category: str | None
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: List[NewsItem]
