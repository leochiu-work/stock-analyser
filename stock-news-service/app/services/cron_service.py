import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories.news_repository import NewsRepository
from app.repositories.ticker_repository import TickerRepository
from app.services.fetch_service import FetchService

logger = logging.getLogger(__name__)


class CronService:
    def __init__(
        self,
        db: Session,
        fetch_service: FetchService,
        ticker_repo: TickerRepository,
        news_repo: NewsRepository,
    ) -> None:
        self.db = db
        self.fetch_service = fetch_service
        self.ticker_repo = ticker_repo
        self.news_repo = news_repo

    def run(self) -> dict[str, dict]:
        """
        For each ticker in the DB, fetch news from last_fetch_date (or 30 days ago)
        to today and upsert. Updates last_fetch_date on success.
        Returns a summary dict keyed by ticker symbol.
        """
        today = date.today()
        tickers = self.ticker_repo.get_all(self.db)

        if not tickers:
            logger.warning("No tickers found in database.")
            return {}

        results: dict[str, dict] = {}

        for ticker in tickers:
            symbol = ticker.symbol
            try:
                from_date = ticker.last_fetch_date or (today - timedelta(days=30))
                to_date = today

                logger.info("%s: fetching news %s → %s", symbol, from_date, to_date)
                records = self.fetch_service.fetch_news(symbol, from_date, to_date)
                count = self.news_repo.upsert_many(self.db, records)
                self.ticker_repo.update_last_fetch_date(self.db, symbol, today)

                logger.info("%s: inserted %d news records", symbol, count)
                results[symbol] = {"status": "ok", "count": count}

            except Exception:
                logger.exception("%s: fetch failed", symbol)
                results[symbol] = {"status": "error"}

        return results
