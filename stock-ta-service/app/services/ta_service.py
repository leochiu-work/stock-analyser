import logging

from sqlalchemy.orm import Session

from app.repositories.ta_repository import TARepository
from app.repositories.ticker_repository import TickerRepository
from app.services import price_client, ta_calculator

logger = logging.getLogger(__name__)


def compute_and_store_from_records(db: Session, symbol: str, ohlc_records: list[dict]) -> int:
    """
    Compute TA indicators from provided OHLC records and upsert results.
    Creates ticker row if it doesn't exist.
    Returns number of rows upserted.
    """
    TickerRepository(db).get_or_create(symbol)
    db.commit()

    if not ohlc_records:
        logger.warning("No OHLC data for %s — skipping TA computation", symbol)
        return 0

    ta_records = ta_calculator.compute(symbol, ohlc_records)
    count = TARepository(db).upsert_many(ta_records)
    logger.info("Upserted %d TA rows for %s", count, symbol)
    return count


def compute_and_store(db: Session, symbol: str) -> int:
    """
    Fetch OHLC history from the price service API, compute TA indicators, and upsert results.
    Returns number of rows upserted.
    """
    ohlc_records = price_client.fetch_ohlc(symbol)
    return compute_and_store_from_records(db, symbol, ohlc_records)
