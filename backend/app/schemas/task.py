"""Pydantic schemas for onboarding tasks and per-employee progress."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    pending = "Pending"
    in_progress = "InProgress"
    completed = "Completed"
    skipped = "Skipped"


class EmployeeTask(BaseModel):
    """A single onboarding task assigned to an employee."""

    model_config = ConfigDict(from_attributes=True)

    employee_task_id: int
    task_id: int
    title: str
    description: str | None = None
    phase: str
    category: str | None = None
    status: TaskStatus
    due_date: date | None = None
    completed_at: datetime | None = None
    is_required: bool = True


class TaskUpdate(BaseModel):
    """Payload to update a task's status (and optional notes)."""

    status: TaskStatus
    notes: str | None = Field(default=None, max_length=1000)


class ChecklistResponse(BaseModel):
    """The full checklist for one employee plus computed progress."""

    employee_id: int
    total: int
    completed: int
    completion_percentage: float
    tasks: list[EmployeeTask]
