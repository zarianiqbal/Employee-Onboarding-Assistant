"""Tests for the SAS-token document upload flow."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_mint_sas_token(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    resp = client.post(
        f"/api/v1/employees/{eid}/documents/sas",
        json={
            "file_name": "passport photo.jpg",
            "content_type": "image/jpeg",
            "document_type": "ID",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # Blob name is sanitized (no spaces) and namespaced under the employee id.
    assert body["blob_name"].startswith(f"{eid}/")
    assert " " not in body["blob_name"]
    assert body["container"] == "employee-documents"
    assert body["required_headers"]["x-ms-blob-type"] == "BlockBlob"


def test_sas_for_missing_employee_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/employees/9999/documents/sas", json={"file_name": "x.pdf"}
    )
    assert resp.status_code == 404


def test_commit_and_list_document(client: TestClient, employee: dict) -> None:
    eid = employee["employee_id"]
    sas = client.post(
        f"/api/v1/employees/{eid}/documents/sas",
        json={"file_name": "w4.pdf", "content_type": "application/pdf"},
    ).json()

    commit = client.post(
        f"/api/v1/employees/{eid}/documents",
        json={
            "blob_name": sas["blob_name"],
            "original_file_name": "w4.pdf",
            "document_type": "TaxForm",
            "content_type": "application/pdf",
            "size_bytes": 2048,
        },
    )
    assert commit.status_code == 201
    assert commit.json()["original_file_name"] == "w4.pdf"

    listing = client.get(f"/api/v1/employees/{eid}/documents")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["document_type"] == "TaxForm"
