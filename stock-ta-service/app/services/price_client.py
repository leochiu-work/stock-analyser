import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def fetch_ohlc(symbol: str) -> list[dict]:
    """Fetch full OHLC history from stock-price-service, paginating as needed."""
    base_url = settings.price_service_base_url
    url = f"{base_url}/api/v1/stocks/{symbol.upper()}"
    all_records: list[dict] = []
    offset = 0
    page_size = 500

    with httpx.Client(timeout=30.0) as client:
        while True:
            resp = client.get(url, params={"limit": page_size, "offset": offset})
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            all_records.extend(items)

            total = data.get("total", 0)
            offset += len(items)
            if offset >= total or not items:
                break

    logger.info("Fetched %d OHLC records for %s", len(all_records), symbol)
    return all_records
