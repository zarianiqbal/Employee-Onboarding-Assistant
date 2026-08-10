"""Tests for the onboarding checklist and task updates."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_checklist_is_assigned_on_first_read(client: TestClient, employee: dict) -> None:
    resp = client.get(f"/api/v1/employees/{employee['employee_id']}/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 13  # full catalog
    assert body["completed"] == 0
    assert body["completion_percentage"] == 0.0
    # Due dates are computed from the start date.
    assert body["tasks"][0]["due_date"] is not None


def test_completing_a_task_updates_progress(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    checklist = client.get(f"/api/v1/employees/{eid}/tasks").json()
    first = checklist["tasks"][0]["employee_task_id"]

    upd = client.patch(f"/api/v1/tasks/{first}", json={"status": "Completed"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "Completed"
    assert upd.json()["completed_at"] is not None

    after = client.get(f"/api/v1/employees/{eid}/tasks").json()
    assert after["completed"] == 1
    assert after["completion_percentage"] > 0


def test_update_missing_task_returns_404(client: TestClient) -> None:
    assert client.patch("/api/v1/tasks/9999", json={"status": "Completed"}).status_code == 404


def test_invalid_status_rejected(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    first = client.get(f"/api/v1/employees/{eid}/tasks").json()["tasks"][0][
        "employee_task_id"
    ]
    resp = client.patch(f"/api/v1/tasks/{first}", json={"status": "Bogus"})
    assert resp.status_code == 422


def test_checklist_for_missing_employee_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/employees/9999/tasks").status_code == 404
