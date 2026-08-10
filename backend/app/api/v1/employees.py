"""Employee registration and profile endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import repository
from app.db.repository import NotFoundError, Repository
from app.schemas.employee import Employee, EmployeeCreate, EmployeeUpdate
from app.schemas.task import ChecklistResponse
from app.services import task_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=Employee, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, repo: Repository = Depends(repository)) -> Employee:
    """Register a new hire.

    In the full flow this record is created with InvitationStatus=
    'PendingAcceptance' and a Microsoft Graph B2B invite is sent to the personal
    email; the status flips to 'Accepted' after the user redeems it.
    """
    created = repo.create_employee(payload.model_dump())
    return Employee.model_validate(created)


@router.get("", response_model=list[Employee])
def list_employees(
    repo: Repository = Depends(repository),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Employee]:
    """List employees (paginated)."""
    return [Employee.model_validate(e) for e in repo.list_employees(limit, offset)]


@router.get("/{employee_id}", response_model=Employee)
def get_employee(employee_id: int, repo: Repository = Depends(repository)) -> Employee:
    """Fetch a single employee profile."""
    try:
        return Employee.model_validate(repo.get_employee(employee_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: int, payload: EmployeeUpdate, repo: Repository = Depends(repository)
) -> Employee:
    """Progressive profiling: update any subset of profile fields."""
    try:
        updated = repo.update_employee(employee_id, payload.model_dump(exclude_unset=True))
        return Employee.model_validate(updated)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{employee_id}/tasks", response_model=ChecklistResponse)
def get_employee_checklist(
    employee_id: int, repo: Repository = Depends(repository)
) -> ChecklistResponse:
    """Return the employee's onboarding checklist with completion percentage."""
    try:
        return task_service.get_checklist(repo, employee_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
