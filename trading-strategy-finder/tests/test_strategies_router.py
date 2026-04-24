"""Tests for /api/v1/strategies router."""
from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient


API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY}


def _make_orm_strategy(
    ticker: str = "AAPL",
    status: str = "completed",
    strategy_id: uuid.UUID | None = None,
) -> SimpleNamespace:
    """Return a plain namespace that satisfies StrategyResponse.model_validate(from_attributes=True)."""
    return SimpleNamespace(
        id=strategy_id or uuid.uuid4(),
        ticker=ticker,
        status=status,
        hypothesis=None,
        sharpe_ratio=None,
        total_return_pct=None,
        max_drawdown_pct=None,
        win_rate_pct=None,
        num_trades=None,
        backtest_start=None,
        backtest_end=None,
        ai_evaluation=None,
        ai_score=None,
        approved=False,
        rejection_reason=None,
        raw_output=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestStrategiesRouter:
    def test_post_research_returns_200(self, test_client: TestClient):
        strategy = _make_orm_strategy()
        with patch(
            "app.routers.strategies.strategy_service.run_research",
            return_value=[strategy],
        ):
            resp = test_client.post(
                "/api/v1/strategies/research",
                json={"ticker": "AAPL"},
                headers=HEADERS,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["ticker"] == "AAPL"
        assert body[0]["status"] == "completed"

    def test_post_research_409_when_already_running(self, test_client: TestClient):
        from fastapi import HTTPException

        with patch(
            "app.routers.strategies.strategy_service.run_research",
            side_effect=HTTPException(status_code=409, detail="Already running"),
        ):
            resp = test_client.post(
                "/api/v1/strategies/research",
                json={"ticker": "AAPL"},
                headers=HEADERS,
            )
        assert resp.status_code == 409

    def test_get_list_returns_200(self, test_client: TestClient):
        strategies = [_make_orm_strategy("AAPL"), _make_orm_strategy("TSLA")]
        with patch("app.routers.strategies.strategy_repository.list_all", return_value=strategies):
            resp = test_client.get("/api/v1/strategies/", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2

    def test_get_by_id_returns_200(self, test_client: TestClient):
        sid = uuid.uuid4()
        strategy = _make_orm_strategy(strategy_id=sid)
        with patch("app.routers.strategies.strategy_repository.get_by_id", return_value=strategy):
            resp = test_client.get(f"/api/v1/strategies/{sid}", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(sid)
        assert body["ticker"] == "AAPL"

    def test_get_by_id_returns_404_when_missing(self, test_client: TestClient):
        with patch("app.routers.strategies.strategy_repository.get_by_id", return_value=None):
            resp = test_client.get(
                f"/api/v1/strategies/{uuid.uuid4()}", headers=HEADERS
            )
        assert resp.status_code == 404

    def test_delete_returns_204(self, test_client: TestClient):
        sid = uuid.uuid4()
        with patch("app.routers.strategies.strategy_repository.delete", return_value=True):
            resp = test_client.delete(f"/api/v1/strategies/{sid}", headers=HEADERS)
        assert resp.status_code == 204

    def test_delete_returns_404_when_missing(self, test_client: TestClient):
        with patch("app.routers.strategies.strategy_repository.delete", return_value=False):
            resp = test_client.delete(
                f"/api/v1/strategies/{uuid.uuid4()}", headers=HEADERS
            )
        assert resp.status_code == 404

    def test_missing_api_key_returns_401(self, test_client: TestClient):
        resp = test_client.get("/api/v1/strategies/")
        assert resp.status_code == 401

    def test_wrong_api_key_returns_401(self, test_client: TestClient):
        resp = test_client.get(
            "/api/v1/strategies/", headers={"X-API-Key": "wrong-key"}
        )
        assert resp.status_code == 401

    def test_health_endpoint_no_auth(self, test_client: TestClient):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
