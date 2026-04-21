from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.ta_repository import TARepository
from app.schemas.ta_indicator import TAIndicatorListResponse, TAIndicatorResponse

router = APIRouter(prefix="/api/v1/ta", tags=["ta"])


@router.get("/{ticker}", response_model=TAIndicatorListResponse)
def get_ta_indicators(
    ticker: str,
    start_date: Annotated[date | None, Query(description="Filter from this date (inclusive)")] = None,
    end_date: Annotated[date | None, Query(description="Filter to this date (inclusive)")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    db: Session = Depends(get_db),
) -> TAIndicatorListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    items = TARepository(db).get_by_ticker(ticker.upper(), start_date, end_date, offset, limit)
    return TAIndicatorListResponse(
        ticker=ticker.upper(),
        items=[TAIndicatorResponse.model_validate(item) for item in items],
    )


@router.get("/{ticker}/latest", response_model=TAIndicatorResponse)
def get_latest_ta(
    ticker: str,
    db: Session = Depends(get_db),
) -> TAIndicatorResponse:
    row = TARepository(db).get_latest(ticker.upper())
    if row is None:
        raise HTTPException(status_code=404, detail=f"No TA data found for {ticker.upper()}")
    return TAIndicatorResponse.model_validate(row)
