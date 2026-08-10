"""Secure document upload endpoints (SAS token mint + reference commit)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import repository
from app.db.repository import NotFoundError, Repository
from app.schemas.document import (
    DocumentCommit,
    DocumentRecord,
    SasTokenRequest,
    SasTokenResponse,
)
from app.services import sas_service

router = APIRouter(prefix="/employees/{employee_id}/documents", tags=["documents"])


@router.post("/sas", response_model=SasTokenResponse)
def create_upload_token(
    employee_id: int, payload: SasTokenRequest, repo: Repository = Depends(repository)
) -> SasTokenResponse:
    """Mint a short-lived, write-only SAS token for a direct-to-blob upload."""
    try:
        repo.get_employee(employee_id)  # ensure the employee exists first
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return sas_service.generate_upload_sas(employee_id, payload)


@router.post("", response_model=DocumentRecord, status_code=status.HTTP_201_CREATED)
def commit_document(
    employee_id: int, payload: DocumentCommit, repo: Repository = Depends(repository)
) -> DocumentRecord:
    """Persist a blob reference after the browser finishes uploading.

    Only metadata is stored; the file itself lives in Blob Storage.
    """
    record = {
        "document_type": payload.document_type,
        "original_file_name": payload.original_file_name,
        "container_name": sas_service.get_settings().documents_container,
        "blob_uri": sas_service.blob_uri(payload.blob_name),
        "content_type": payload.content_type,
        "size_bytes": payload.size_bytes,
    }
    try:
        created = repo.add_document(employee_id, record)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DocumentRecord.model_validate(created)


@router.get("", response_model=list[DocumentRecord])
def list_documents(
    employee_id: int, repo: Repository = Depends(repository)
) -> list[DocumentRecord]:
    """List an employee's uploaded documents (metadata only)."""
    return [DocumentRecord.model_validate(d) for d in repo.list_documents(employee_id)]
