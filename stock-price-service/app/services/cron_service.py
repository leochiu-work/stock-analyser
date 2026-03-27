import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.stock_price_repository import StockPriceRepository
from app.repositories.ticker_repository import TickerRepository
from app.services.fetch_service import FetchService

logger = logging.getLogger(__name__)


class CronService:
    def __init__(self, db: Session, fetch_service: FetchService | None = None) -> None:
        self.stock_repo = StockPriceRepository(db)
        self.ticker_repo = TickerRepository(db)
        self.fetch_service = fetch_service or FetchService()

    def run(self) -> dict[str, dict]:
        """
        For each ticker in the DB, fetch prices from last_fetch_date+1 to today
        and upsert into stock_prices. Updates last_fetch_date on success.
        Returns a summary dict keyed by ticker symbol.
        """
        today = date.today()
        tickers = self.ticker_repo.get_all()

        if not tickers:
            logger.warning("No tickers found in database.")
            return {}

        results: dict[str, dict] = {}

        for ticker in tickers:
            symbol = ticker.symbol
            try:
                last = ticker.last_fetch_date

                if last is not None and last >= today:
                    logger.info("%s: already up to date (last_fetch_date=%s)", symbol, last)
                    results[symbol] = {"status": "skipped", "reason": "already up to date"}
                    continue

                # Determine fetch window
                if last is None:
                    fetch_from = settings.default_start_date
                else:
                    fetch_from = last + timedelta(days=1)

                logger.info("%s: fetching %s → %s", symbol, fetch_from, today)
                records = self.fetch_service.fetch_prices(symbol, fetch_from, today)
                count = self.stock_repo.upsert_many(records)
                self.ticker_repo.update_last_fetch_date(symbol, today)

                logger.info("%s: upserted %d records", symbol, count)
                results[symbol] = {"status": "ok", "records_upserted": count}

            except Exception:
                logger.exception("%s: fetch failed", symbol)
                results[symbol] = {"status": "error"}

        return results
