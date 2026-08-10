"""Secure document upload via short-lived SAS tokens (the "valet key" pattern).

The backend never proxies file bytes. Instead it mints a short-lived,
write-only Shared Access Signature scoped to a single blob and hands it to the
browser, which uploads directly to Azure Blob Storage. The SAS is signed with a
**user-delegation key** derived from the App Service managed identity — not the
storage account key — so no static storage secret is ever used.

In local mode (no storage configured) a stub upload URL is returned so the
frontend upload flow can be exercised without a cloud account.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.schemas.document import SasTokenRequest, SasTokenResponse

logger = logging.getLogger(__name__)

# How long an upload token is valid. Short by design.
_SAS_TTL = timedelta(minutes=15)
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_blob_name(employee_id: int, file_name: str) -> str:
    """Namespace uploads by employee and prefix a UUID to prevent collisions."""
    cleaned = _SAFE_NAME.sub("_", file_name).strip("_") or "file"
    return f"{employee_id}/{uuid.uuid4().hex}-{cleaned}"


def generate_upload_sas(employee_id: int, req: SasTokenRequest) -> SasTokenResponse:
    """Mint a write-only SAS token for a single blob in the documents container."""
    settings = get_settings()
    blob_name = _safe_blob_name(employee_id, req.file_name)
    container = settings.documents_container
    expires_at = datetime.now(UTC) + _SAS_TTL

    required_headers = {"x-ms-blob-type": "BlockBlob", "Content-Type": req.content_type}

    if not settings.storage_configured:
        logger.warning("Storage not configured — returning stub SAS for %s", blob_name)
        stub_url = (
            f"https://localhost/devstoreaccount1/{container}/{blob_name}"
            f"?stub-sas&se={expires_at.isoformat()}"
        )
        return SasTokenResponse(
            upload_url=stub_url,
            blob_name=blob_name,
            container=container,
            expires_at=expires_at,
            required_headers=required_headers,
        )

    from azure.storage.blob import (
        BlobSasPermissions,
        BlobServiceClient,
        generate_blob_sas,
    )

    from app.core.azure_clients import get_credential

    service = BlobServiceClient(
        account_url=settings.azure_storage_account_url, credential=get_credential()
    )
    # User-delegation key is issued by Entra ID on behalf of the managed
    # identity; it signs the SAS without ever touching the account key.
    delegation_key = service.get_user_delegation_key(
        key_start_time=datetime.now(UTC) - timedelta(minutes=5),
        key_expiry_time=expires_at,
    )
    sas = generate_blob_sas(
        account_name=service.account_name,
        container_name=container,
        blob_name=blob_name,
        user_delegation_key=delegation_key,
        permission=BlobSasPermissions(write=True, create=True),  # write-only
        expiry=expires_at,
        start=datetime.now(UTC) - timedelta(minutes=5),
    )
    upload_url = f"{settings.azure_storage_account_url.rstrip('/')}/{container}/{blob_name}?{sas}"
    return SasTokenResponse(
        upload_url=upload_url,
        blob_name=blob_name,
        container=container,
        expires_at=expires_at,
        required_headers=required_headers,
    )


def blob_uri(blob_name: str) -> str:
    """Return the canonical (token-less) blob URI for persistence."""
    settings = get_settings()
    base = settings.azure_storage_account_url or "https://localhost/devstoreaccount1"
    return f"{base.rstrip('/')}/{settings.documents_container}/{blob_name}"
