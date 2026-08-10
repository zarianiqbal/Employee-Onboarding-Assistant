"""Aggregates the v1 endpoint routers.

Endpoint modules are added incrementally as features land (employees, tasks,
documents, chat).
"""
from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()
