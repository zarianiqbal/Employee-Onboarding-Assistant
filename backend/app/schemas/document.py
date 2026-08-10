"""Pydantic schemas for the secure document upload (SAS token) flow."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SasTokenRequest(BaseModel):
    """Request for a short-lived, write-only upload token."""

    file_name: str = Field(min_length=1, max_length=400)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    document_type: str = Field(default="Other", max_length=60)


class SasTokenResponse(BaseModel):
    """A minted SAS token the browser uses to upload directly to Blob Storage."""

    upload_url: str
    blob_name: str
    container: str
    expires_at: datetime
    # The browser must send this header so the stored content type is correct.
    required_headers: dict[str, str]


class DocumentRecord(BaseModel):
    """A stored blob reference (metadata only; the file lives in Blob Storage)."""

    document_id: int
    employee_id: int
    document_type: str
    original_file_name: str
    container_name: str
    blob_uri: str
    content_type: str | None = None
    size_bytes: int | None = None
    uploaded_at: datetime


class DocumentCommit(BaseModel):
    """Called after a successful direct-to-blob upload to persist the reference."""

    blob_name: str = Field(min_length=1, max_length=400)
    original_file_name: str = Field(min_length=1, max_length=400)
    document_type: str = Field(default="Other", max_length=60)
    content_type: str | None = Field(default=None, max_length=120)
    size_bytes: int | None = None
