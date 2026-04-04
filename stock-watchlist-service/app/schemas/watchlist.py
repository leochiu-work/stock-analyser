from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class WatchlistTickerItem(BaseModel):
    symbol: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistTickerCreate(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def symbol_to_upper(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol must not be empty")
        return v


class WatchlistResponse(BaseModel):
    total: int
    items: list[WatchlistTickerItem]
