from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.watchlist import WatchlistResponse, WatchlistTickerCreate, WatchlistTickerItem
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("", response_model=WatchlistResponse)
def get_watchlist(db: Session = Depends(get_db)) -> WatchlistResponse:
    service = WatchlistService(db)
    return service.get_all()


@router.post("", response_model=WatchlistTickerItem, status_code=201)
def add_ticker(
    body: WatchlistTickerCreate,
    db: Session = Depends(get_db),
) -> WatchlistTickerItem:
    service = WatchlistService(db)
    return service.add_ticker(body.symbol)


@router.delete("/{symbol}", status_code=204)
def delete_ticker(symbol: str, db: Session = Depends(get_db)) -> Response:
    service = WatchlistService(db)
    found = service.remove_ticker(symbol)
    if not found:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return Response(status_code=204)
