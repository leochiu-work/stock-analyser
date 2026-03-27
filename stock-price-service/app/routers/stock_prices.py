from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stock_price import StockPriceListResponse
from app.services.stock_price_service import StockPriceService

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@router.get("/{ticker}", response_model=StockPriceListResponse)
def get_ticker_prices(
    ticker: str,
    start_date: Annotated[date | None, Query(description="Filter from this date (inclusive)")] = None,
    end_date: Annotated[date | None, Query(description="Filter until this date (inclusive)")] = None,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=500, description="Max records to return")] = 50,
    db: Session = Depends(get_db),
) -> StockPriceListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    service = StockPriceService(db)
    return service.get_prices(ticker, start_date, end_date, offset, limit)
