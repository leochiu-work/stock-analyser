"""Tests for /api/v1/strategies router."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.strategy import Strategy


API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY}


def _make_orm_strategy(
    ticker: str = "AAPL",
    status: str = "completed",
    strategy_id: uuid.UUID | None = None,
) -> Strategy:
    s = Strategy.__new__(Strategy)
    s.id = strategy_id or uuid.uuid4()
    s.ticker = ticker
    s.status = status
    s.name = None
    s.description = None
    s.iterations = 1
    s.parameters = None
    s.created_at = datetime.utcnow()
    s.updated_at = datetime.utcnow()
    return s


class TestStrategiesRouter:
    def test_post_research_returns_200(self, test_client: TestClient):
        strategy = _make_orm_strategy()
        with patch("app.routers.strategies.strategy_service.run_research", return_value=strategy):
            resp = test_client.post(
                "/api/v1/strategies/research",
                json={"ticker": "AAPL"},
                headers=HEADERS,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ticker"] == "AAPL"
        assert body["status"] == "completed"

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
        with (
            patch("app.routers.strategies.strategy_repository.get_by_id", return_value=strategy),
            patch("app.routers.strategies.backtest_repository.get_best_by_strategy", return_value=None),
        ):
            resp = test_client.get(f"/api/v1/strategies/{sid}", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(sid)
        assert body["latest_result"] is None

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
