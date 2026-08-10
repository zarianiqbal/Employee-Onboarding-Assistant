"""Schemas for the Entra ID B2B invitation + redemption flow."""
from __future__ import annotations

from pydantic import BaseModel


class InvitationResponse(BaseModel):
    """Result of sending a B2B invitation."""

    invited_email: str
    redeem_url: str
    status: str
    stub: bool = False


class RedeemRequest(BaseModel):
    """Sent by the frontend after SSO to finalize the employee's profile.

    The caller's identity comes from the validated JWT (or the debug header in
    local mode), not from the body — the body only names which employee record
    the authenticated user is redeeming.
    """

    employee_id: int
