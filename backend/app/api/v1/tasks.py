"""Onboarding task endpoints (checklist status updates)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import repository
from app.db.repository import NotFoundError, Repository
from app.schemas.task import EmployeeTask, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.patch("/{employee_task_id}", response_model=EmployeeTask)
def update_task(
    employee_task_id: int, payload: TaskUpdate, repo: Repository = Depends(repository)
) -> EmployeeTask:
    """Update a task's status (e.g. check it off).

    Powers the interactive checklist: the UI optimistically toggles a task and
    calls this endpoint to persist the definitive status. Setting status to
    'Completed' stamps the completion timestamp server-side.
    """
    try:
        return task_service.update_task(repo, employee_task_id, payload.status, payload.notes)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
