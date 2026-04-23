from __future__ import annotations

from datetime import date

import httpx

from app.config import settings


def get_indicators(ticker: str, start_date: date, end_date: date) -> list[dict]:
    url = f"{settings.ta_service_base_url}/api/v1/ta/{ticker}"
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "limit": 500,
    }
    with httpx.Client() as client:
        response = client.get(url, params=params)
        response.raise_for_status()
    return response.json()["items"]
