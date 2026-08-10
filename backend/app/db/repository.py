"""Repository abstraction over the onboarding data store.

Defines the `Repository` protocol used by the service layer and an
`InMemoryRepository` implementation used in local mode / tests. The SQL-backed
implementation (`sql_repository.SqlRepository`) mirrors this interface against
Azure SQL. The factory `get_repository()` returns the right one based on config.
"""
from __future__ import annotations

import threading
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from app.db.catalog import TASK_CATALOG


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""


class Repository(Protocol):
    """Data-access interface for the onboarding domain."""

    def create_employee(self, data: dict) -> dict: ...
    def get_employee(self, employee_id: int) -> dict: ...
    def update_employee(self, employee_id: int, changes: dict) -> dict: ...
    def list_employees(self, limit: int, offset: int) -> list[dict]: ...

    def get_checklist(self, employee_id: int) -> list[dict]: ...
    def update_task(self, employee_task_id: int, status: str, notes: str | None) -> dict: ...

    def add_document(self, employee_id: int, record: dict) -> dict: ...
    def list_documents(self, employee_id: int) -> list[dict]: ...

    def save_message(self, employee_id: int, role: str, content: str) -> None: ...


def _now() -> datetime:
    return datetime.now(UTC)


class InMemoryRepository:
    """A thread-safe in-memory store seeded with the standard task catalog.

    Assigning tasks is lazy: the first time an employee's checklist is read, the
    full active catalog is materialized for them (matching how the SQL seed
    cross-joins employees with tasks).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._employees: dict[int, dict] = {}
        self._employee_tasks: dict[int, dict] = {}
        self._documents: dict[int, dict] = {}
        self._messages: list[dict] = []
        self._emp_seq = 0
        self._task_seq = 0
        self._doc_seq = 0

    # --- Employees --------------------------------------------------------
    def create_employee(self, data: dict) -> dict:
        with self._lock:
            self._emp_seq += 1
            now = _now()
            employee = {
                "employee_id": self._emp_seq,
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "personal_email": data["personal_email"],
                "job_title": data.get("job_title"),
                "department": data.get("department"),
                "region": data.get("region"),
                "clearance_level": data.get("clearance_level"),
                "start_date": data.get("start_date"),
                "date_of_birth": None,
                "phone_number": None,
                "home_address": None,
                "invitation_status": "PendingAcceptance",
                "created_at": now,
                "updated_at": now,
            }
            self._employees[employee["employee_id"]] = employee
            return dict(employee)

    def get_employee(self, employee_id: int) -> dict:
        employee = self._employees.get(employee_id)
        if employee is None:
            raise NotFoundError(f"Employee {employee_id} not found")
        return dict(employee)

    def update_employee(self, employee_id: int, changes: dict) -> dict:
        with self._lock:
            employee = self._employees.get(employee_id)
            if employee is None:
                raise NotFoundError(f"Employee {employee_id} not found")
            for key, value in changes.items():
                if value is not None:
                    employee[key] = value
            employee["updated_at"] = _now()
            return dict(employee)

    def list_employees(self, limit: int, offset: int) -> list[dict]:
        ordered = sorted(self._employees.values(), key=lambda e: e["employee_id"])
        return [dict(e) for e in ordered[offset : offset + limit]]

    # --- Checklist / tasks ------------------------------------------------
    def _assign_catalog(self, employee_id: int) -> None:
        """Materialize the active task catalog for an employee (once)."""
        already = any(t["employee_id"] == employee_id for t in self._employee_tasks.values())
        if already:
            return
        employee = self._employees[employee_id]
        start: date | None = employee.get("start_date")
        for task in TASK_CATALOG:
            self._task_seq += 1
            due = start + timedelta(days=task["due_offset_days"]) if start else None
            self._employee_tasks[self._task_seq] = {
                "employee_task_id": self._task_seq,
                "employee_id": employee_id,
                "task_id": task["task_id"],
                "title": task["title"],
                "description": task["description"],
                "phase": task["phase"],
                "category": task["category"],
                "is_required": task["is_required"],
                "sort_order": task["sort_order"],
                "status": "Pending",
                "due_date": due,
                "completed_at": None,
                "notes": None,
            }

    def get_checklist(self, employee_id: int) -> list[dict]:
        with self._lock:
            if employee_id not in self._employees:
                raise NotFoundError(f"Employee {employee_id} not found")
            self._assign_catalog(employee_id)
            tasks = [
                dict(t)
                for t in self._employee_tasks.values()
                if t["employee_id"] == employee_id
            ]
            tasks.sort(key=lambda t: t["sort_order"])
            return tasks

    def update_task(self, employee_task_id: int, status: str, notes: str | None) -> dict:
        with self._lock:
            task = self._employee_tasks.get(employee_task_id)
            if task is None:
                raise NotFoundError(f"Task {employee_task_id} not found")
            task["status"] = status
            task["completed_at"] = _now() if status == "Completed" else None
            if notes is not None:
                task["notes"] = notes
            return dict(task)

    # --- Documents --------------------------------------------------------
    def add_document(self, employee_id: int, record: dict) -> dict:
        with self._lock:
            if employee_id not in self._employees:
                raise NotFoundError(f"Employee {employee_id} not found")
            self._doc_seq += 1
            doc = {
                "document_id": self._doc_seq,
                "employee_id": employee_id,
                "uploaded_at": _now(),
                **record,
            }
            self._documents[self._doc_seq] = doc
            return dict(doc)

    def list_documents(self, employee_id: int) -> list[dict]:
        docs = [
            dict(d) for d in self._documents.values() if d["employee_id"] == employee_id
        ]
        docs.sort(key=lambda d: d["document_id"])
        return docs

    # --- Chat -------------------------------------------------------------
    def save_message(self, employee_id: int, role: str, content: str) -> None:
        with self._lock:
            self._messages.append(
                {
                    "employee_id": employee_id,
                    "role": role,
                    "content": content,
                    "created_at": _now(),
                }
            )
