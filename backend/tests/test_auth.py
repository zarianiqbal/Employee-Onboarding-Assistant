"""Tests for the Entra ID B2B invitation + redemption flow (local mode)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_invite_returns_stub_redeem_url(client: TestClient, employee: dict) -> None:
    resp = client.post(f"/api/v1/employees/{employee['employee_id']}/invite")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stub"] is True
    assert body["invited_email"] == employee["personal_email"]
    assert body["redeem_url"]
    assert body["status"] == "PendingAcceptance"


def test_invite_missing_employee_404(client: TestClient) -> None:
    assert client.post("/api/v1/employees/9999/invite").status_code == 404


def test_redeem_flips_status_to_accepted(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    assert employee["invitation_status"] == "PendingAcceptance"

    resp = client.post(
        "/api/v1/auth/redeem",
        json={"employee_id": eid},
        headers={"X-Debug-Object-Id": "entra-oid-123"},
    )
    assert resp.status_code == 200
    assert resp.json()["invitation_status"] == "Accepted"


def test_redeem_missing_employee_404(client: TestClient) -> None:
    resp = client.post("/api/v1/auth/redeem", json={"employee_id": 9999})
    assert resp.status_code == 404
