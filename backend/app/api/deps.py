"""Shared FastAPI dependencies."""
from __future__ import annotations

from app.db.factory import get_repository
from app.db.repository import Repository


def repository() -> Repository:
    """Provide the process-wide repository to endpoints."""
    return get_repository()
