"""
Cron job entry point. Intended to be invoked by an external scheduler (e.g. k8s CronJob).

Usage:
    python cron.py
"""

import logging
import sys

from app.config import settings
from app.database import SessionLocal
from app.repositories.news_repository import NewsRepository
from app.repositories.ticker_repository import TickerRepository
from app.services.cron_service import CronService
from app.services.fetch_service import FetchService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    db = SessionLocal()
    try:
        fetch_service = FetchService(api_key=settings.FINNHUB_API_KEY)
        ticker_repo = TickerRepository()
        news_repo = NewsRepository()
        service = CronService(db, fetch_service, ticker_repo, news_repo)
        results = service.run()
        if not results:
            logger.info("No tickers to process.")
            return
        errors = [s for s, r in results.items() if r.get("status") == "error"]
        for symbol, result in results.items():
            logger.info("%-10s %s", symbol, result)
        if errors:
            logger.error("Failed tickers: %s", errors)
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
