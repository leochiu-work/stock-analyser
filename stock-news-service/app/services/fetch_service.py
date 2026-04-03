from datetime import date, datetime, timezone

import finnhub


class FetchService:
    def __init__(self, api_key: str) -> None:
        self.client = finnhub.Client(api_key=api_key)

    def fetch_news(self, symbol: str, from_date: date, to_date: date) -> list[dict]:
        """
        Fetch company news for a ticker from Finnhub.
        Returns a list of dicts ready for DB insertion.
        """
        raw = self.client.company_news(
            symbol,
            _from=from_date.isoformat(),
            to=to_date.isoformat(),
        )

        if not raw:
            return []

        records = []
        for item in raw:
            records.append(
                {
                    "ticker_symbol": symbol.upper(),
                    "finnhub_id": item["id"],
                    "headline": item.get("headline", ""),
                    "summary": item.get("summary") or None,
                    "source": item.get("source") or None,
                    "url": item.get("url") or None,
                    "image": item.get("image") or None,
                    "category": item.get("category") or None,
                    "published_at": datetime.fromtimestamp(
                        item["datetime"], tz=timezone.utc
                    ).replace(tzinfo=None),
                }
            )
        return records
