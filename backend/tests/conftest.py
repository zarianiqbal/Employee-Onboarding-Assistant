"""Shared pytest fixtures.

Each test gets a fresh in-memory repository by clearing the cached factory
singleton, so state never leaks between tests.
"""
from __future__ import annotations

import pytest
from app.db import factory
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_repository():
    factory.get_repository.cache_clear()
    yield
    factory.get_repository.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def employee(client: TestClient) -> dict:
    """Create and return a registered employee for tests to build on."""
    resp = client.post(
        "/api/v1/employees",
        json={
            "first_name": "Test",
            "last_name": "User",
            "personal_email": "test.user@example.com",
            "department": "Engineering",
            "region": "US",
            "start_date": "2026-09-01",
        },
    )
    assert resp.status_code == 201
    return resp.json()
