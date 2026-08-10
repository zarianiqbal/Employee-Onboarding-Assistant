"""Entra ID B2B invitation + redemption endpoints (federated authentication)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import repository
from app.core.auth import Principal, verify_token
from app.db.repository import NotFoundError, Repository
from app.schemas.auth import InvitationResponse, RedeemRequest
from app.schemas.employee import Employee
from app.services import graph_service

router = APIRouter(tags=["auth"])


@router.post("/employees/{employee_id}/invite", response_model=InvitationResponse)
def invite_employee(
    employee_id: int, repo: Repository = Depends(repository)
) -> InvitationResponse:
    """Send a Microsoft Graph B2B invitation to a registered new hire.

    Creates a one-time redemption link delivered to the employee's personal
    email; the record stays at InvitationStatus='PendingAcceptance' until they
    redeem it and sign in.
    """
    try:
        employee = repo.get_employee(employee_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = graph_service.send_invitation(employee)
    return InvitationResponse(**result)


@router.post("/auth/redeem", response_model=Employee)
def redeem_invitation(
    payload: RedeemRequest,
    principal: Principal = Depends(verify_token),
    repo: Repository = Depends(repository),
) -> Employee:
    """Finalize onboarding after SSO: flip the record to 'Accepted'.

    The verified Entra object id comes from the validated JWT (or the debug
    header in local mode) and is recorded against the employee profile.
    """
    try:
        updated = repo.accept_invitation(payload.employee_id, principal.object_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Employee.model_validate(updated)
