"""Tests for employee registration and profile endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_employee_defaults_to_pending(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/employees",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "personal_email": "ada@example.com",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["employee_id"] >= 1
    assert body["invitation_status"] == "PendingAcceptance"


def test_register_rejects_invalid_email(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/employees",
        json={"first_name": "X", "last_name": "Y", "personal_email": "not-an-email"},
    )
    assert resp.status_code == 422


def test_register_requires_names(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/employees",
        json={"first_name": "", "last_name": "Y", "personal_email": "a@example.com"},
    )
    assert resp.status_code == 422


def test_get_employee(client: TestClient, employee: dict) -> None:
    resp = client.get(f"/api/v1/employees/{employee['employee_id']}")
    assert resp.status_code == 200
    assert resp.json()["personal_email"] == "test.user@example.com"


def test_get_missing_employee_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/employees/9999").status_code == 404


def test_progressive_profiling_update(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    resp = client.patch(
        f"/api/v1/employees/{eid}",
        json={"home_address": "1 Infinite Loop", "phone_number": "555-0100"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["home_address"] == "1 Infinite Loop"
    assert body["phone_number"] == "555-0100"


def test_list_employees_pagination(client: TestClient) -> None:
    for i in range(3):
        client.post(
            "/api/v1/employees",
            json={
                "first_name": f"User{i}",
                "last_name": "Test",
                "personal_email": f"user{i}@example.com",
            },
        )
    resp = client.get("/api/v1/employees?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
