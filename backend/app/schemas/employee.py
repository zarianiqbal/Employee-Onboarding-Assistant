"""Pydantic schemas for employee registration and profiles."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationStatus(str, Enum):
    pending = "PendingAcceptance"
    accepted = "Accepted"
    revoked = "Revoked"


class EmployeeCreate(BaseModel):
    """Payload HR submits to register / invite a new hire.

    Only the first name, last name, and personal email are required; everything
    else supports progressive profiling and may be filled in later.
    """

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    personal_email: EmailStr
    job_title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=60)
    clearance_level: str | None = Field(default=None, max_length=40)
    start_date: date | None = None


class EmployeeUpdate(BaseModel):
    """Partial update — any subset of profile fields (progressive profiling)."""

    job_title: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=60)
    clearance_level: str | None = Field(default=None, max_length=40)
    start_date: date | None = None
    date_of_birth: date | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    home_address: str | None = Field(default=None, max_length=400)


class Employee(BaseModel):
    """An employee profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    first_name: str
    last_name: str
    personal_email: EmailStr
    job_title: str | None = None
    department: str | None = None
    region: str | None = None
    clearance_level: str | None = None
    start_date: date | None = None
    date_of_birth: date | None = None
    phone_number: str | None = None
    home_address: str | None = None
    invitation_status: InvitationStatus = InvitationStatus.pending
    created_at: datetime
    updated_at: datetime
