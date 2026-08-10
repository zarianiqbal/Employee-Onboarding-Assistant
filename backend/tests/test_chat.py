"""Tests for the AI onboarding assistant chat."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_leave_policy_question_is_grounded(client: TestClient, employee: dict) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={"employee_id": employee["employee_id"], "message": "Explain the leave policy."},
    )
    assert resp.status_code == 200
    body = resp.json()
    titles = {c["title"] for c in body["citations"]}
    assert "Leave Policy" in titles
    assert body["answer"]


def test_documents_question_cites_documents_policy(client: TestClient, employee: dict) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={
            "employee_id": employee["employee_id"],
            "message": "What documents do I need to submit?",
        },
    )
    assert resp.status_code == 200
    titles = {c["title"] for c in resp.json()["citations"]}
    assert "Required Onboarding Documents" in titles


def test_unknown_question_declines_gracefully(client: TestClient, employee: dict) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={
            "employee_id": employee["employee_id"],
            "message": "zxcvbnm qwerty asdfgh",
        },
    )
    assert resp.status_code == 200
    assert "HR" in resp.json()["answer"]


def test_chat_streaming_emits_done_event(client: TestClient, employee: dict) -> None:
    with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"employee_id": employee["employee_id"], "message": "Explain the leave policy."},
    ) as stream:
        body = "".join(stream.iter_text())
    assert "event: done" in body
    assert "citations" in body
    assert "delta" in body
