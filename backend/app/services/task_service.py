"""Business logic for onboarding checklists and task progress."""
from __future__ import annotations

from app.db.repository import Repository
from app.schemas.task import ChecklistResponse, EmployeeTask, TaskStatus


def get_checklist(repo: Repository, employee_id: int) -> ChecklistResponse:
    """Assemble an employee's checklist with a computed completion percentage."""
    rows = repo.get_checklist(employee_id)
    tasks = [EmployeeTask.model_validate(row) for row in rows]

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.completed)
    pct = round((completed / total) * 100, 1) if total else 0.0

    return ChecklistResponse(
        employee_id=employee_id,
        total=total,
        completed=completed,
        completion_percentage=pct,
        tasks=tasks,
    )


def update_task(
    repo: Repository, employee_task_id: int, status: TaskStatus, notes: str | None
) -> EmployeeTask:
    """Update a single task's status; the repo stamps CompletedAt when done."""
    row = repo.update_task(employee_task_id, status.value, notes)
    # The SQL path returns a subset of columns; backfill display fields that the
    # update statement doesn't echo so the response schema is always complete.
    row.setdefault("title", "")
    row.setdefault("phase", "")
    row.setdefault("is_required", True)
    return EmployeeTask.model_validate(row)
