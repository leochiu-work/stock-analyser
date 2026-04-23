"""Tests for /api/v1/documents router."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY}


class TestDocumentsRouter:
    def test_post_document_returns_201(self, test_client: TestClient):
        with (
            patch("app.routers.documents.get_collection"),
            patch(
                "app.routers.documents.document_service.add_document",
                return_value="doc-abc-123",
            ),
        ):
            resp = test_client.post(
                "/api/v1/documents/",
                json={
                    "text": "Buy wonderful businesses at fair prices.",
                    "investor": "buffett",
                    "source": "warren_buffett.md",
                },
                headers=HEADERS,
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == "doc-abc-123"
        assert body["investor"] == "buffett"
        assert body["source"] == "warren_buffett.md"

    def test_get_documents_returns_200(self, test_client: TestClient):
        docs = [
            {"id": "doc-1", "investor": "buffett", "source": "warren_buffett.md"},
            {"id": "doc-2", "investor": "lynch", "source": "peter_lynch.md"},
        ]
        with (
            patch("app.routers.documents.get_collection"),
            patch(
                "app.routers.documents.document_service.list_documents",
                return_value=docs,
            ),
        ):
            resp = test_client.get("/api/v1/documents/", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["investor"] == "buffett"

    def test_delete_document_returns_204(self, test_client: TestClient):
        with (
            patch("app.routers.documents.get_collection"),
            patch("app.routers.documents.document_service.delete_document"),
        ):
            resp = test_client.delete("/api/v1/documents/doc-1", headers=HEADERS)
        assert resp.status_code == 204

    def test_missing_api_key_returns_401(self, test_client: TestClient):
        resp = test_client.get("/api/v1/documents/")
        assert resp.status_code == 401
