from fastapi import APIRouter, Depends
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
