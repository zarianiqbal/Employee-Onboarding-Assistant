"""Tests for the meta / health endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_reports_integrations(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    # In local/test mode every Azure integration is disabled.
    assert set(body["integrations"]) == {"sql", "storage", "openai", "search"}
    assert all(v is False for v in body["integrations"].values())
