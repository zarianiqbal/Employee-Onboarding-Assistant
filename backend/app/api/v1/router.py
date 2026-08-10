"""Aggregates the v1 endpoint routers.

Endpoint modules are added incrementally as features land (employees, tasks,
documents, chat).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import documents, employees, tasks

api_router = APIRouter()
api_router.include_router(employees.router)
api_router.include_router(tasks.router)
api_router.include_router(documents.router)
