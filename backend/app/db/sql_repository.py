"""Azure SQL implementation of the repository (secretless).

Connections authenticate with an Entra access token obtained from
`DefaultAzureCredential` — there is no username/password in the connection
string. The token is passed to the ODBC driver via attribute 1256
(SQL_COPT_SS_ACCESS_TOKEN).

pyodbc and azure-identity are imported lazily so the package remains importable
in local mode where the ODBC driver may be absent.
"""
from __future__ import annotations

import logging
import struct
from contextlib import contextmanager
from typing import Any

from app.core.config import get_settings
from app.db.repository import NotFoundError

logger = logging.getLogger(__name__)

# Azure SQL / Entra token scope and the ODBC access-token attribute id.
_TOKEN_SCOPE = "https://database.windows.net/.default"
_SQL_COPT_SS_ACCESS_TOKEN = 1256


def _encode_token(token: str) -> bytes:
    """Pack an access token into the widechar length-prefixed form ODBC wants."""
    raw = token.encode("utf-16-le")
    return struct.pack("<i", len(raw)) + raw


class SqlRepository:
    """Repository backed by Azure SQL Database via pyodbc."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @contextmanager
    def _connect(self):
        import pyodbc  # lazy

        from app.core.azure_clients import get_credential

        token = get_credential().get_token(_TOKEN_SCOPE).token
        conn_str = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{self._settings.azure_sql_server},1433;"
            f"Database={self._settings.azure_sql_database};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        conn = pyodbc.connect(
            conn_str, attrs_before={_SQL_COPT_SS_ACCESS_TOKEN: _encode_token(token)}
        )
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    # --- Employees --------------------------------------------------------
    def create_employee(self, data: dict) -> dict:
        sql = """
            INSERT INTO Core.Employees
                (FirstName, LastName, PersonalEmail, JobTitle, Department,
                 Region, ClearanceLevel, StartDate)
            OUTPUT INSERTED.EmployeeId
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                sql,
                data["first_name"],
                data["last_name"],
                data["personal_email"],
                data.get("job_title"),
                data.get("department"),
                data.get("region"),
                data.get("clearance_level"),
                data.get("start_date"),
            )
            employee_id = cur.fetchone()[0]
            conn.commit()
        return self.get_employee(employee_id)

    def get_employee(self, employee_id: int) -> dict:
        sql = """
            SELECT EmployeeId AS employee_id, FirstName AS first_name,
                   LastName AS last_name, PersonalEmail AS personal_email,
                   JobTitle AS job_title, Department AS department,
                   Region AS region, ClearanceLevel AS clearance_level,
                   StartDate AS start_date, DateOfBirth AS date_of_birth,
                   PhoneNumber AS phone_number, HomeAddress AS home_address,
                   InvitationStatus AS invitation_status,
                   CreatedAt AS created_at, UpdatedAt AS updated_at
            FROM Core.Employees WHERE EmployeeId = ?;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, employee_id)
            rows = self._rows_as_dicts(cur)
        if not rows:
            raise NotFoundError(f"Employee {employee_id} not found")
        return rows[0]

    def update_employee(self, employee_id: int, changes: dict) -> dict:
        column_map = {
            "job_title": "JobTitle",
            "department": "Department",
            "region": "Region",
            "clearance_level": "ClearanceLevel",
            "start_date": "StartDate",
            "date_of_birth": "DateOfBirth",
            "phone_number": "PhoneNumber",
            "home_address": "HomeAddress",
        }
        sets, params = [], []
        for key, value in changes.items():
            if value is not None and key in column_map:
                sets.append(f"{column_map[key]} = ?")
                params.append(value)
        if sets:
            sets.append("UpdatedAt = SYSUTCDATETIME()")
            params.append(employee_id)
            sql = f"UPDATE Core.Employees SET {', '.join(sets)} WHERE EmployeeId = ?;"
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(sql, *params)
                conn.commit()
        return self.get_employee(employee_id)

    def list_employees(self, limit: int, offset: int) -> list[dict]:
        sql = """
            SELECT EmployeeId AS employee_id, FirstName AS first_name,
                   LastName AS last_name, PersonalEmail AS personal_email,
                   JobTitle AS job_title, Department AS department,
                   Region AS region, ClearanceLevel AS clearance_level,
                   StartDate AS start_date, DateOfBirth AS date_of_birth,
                   PhoneNumber AS phone_number, HomeAddress AS home_address,
                   InvitationStatus AS invitation_status,
                   CreatedAt AS created_at, UpdatedAt AS updated_at
            FROM Core.Employees
            ORDER BY EmployeeId
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, offset, limit)
            return self._rows_as_dicts(cur)

    def accept_invitation(self, employee_id: int, entra_object_id: str) -> dict:
        sql = """
            UPDATE Core.Employees
            SET InvitationStatus = 'Accepted',
                EntraObjectId = ?,
                ExternalUserStateChangeDateTime = SYSUTCDATETIME(),
                UpdatedAt = SYSUTCDATETIME()
            WHERE EmployeeId = ?;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, entra_object_id, employee_id)
            if cur.rowcount == 0:
                raise NotFoundError(f"Employee {employee_id} not found")
            conn.commit()
        return self.get_employee(employee_id)

    # --- Checklist / tasks ------------------------------------------------
    def get_checklist(self, employee_id: int) -> list[dict]:
        # Ensure the catalog is assigned, then read it back.
        assign = """
            INSERT INTO Onboarding.EmployeeTasks (EmployeeId, TaskId, Status, DueDate)
            SELECT e.EmployeeId, t.TaskId, 'Pending',
                   DATEADD(DAY, t.DueOffsetDays, e.StartDate)
            FROM Core.Employees e
            CROSS JOIN Onboarding.Tasks t
            WHERE e.EmployeeId = ? AND t.IsActive = 1
              AND NOT EXISTS (
                  SELECT 1 FROM Onboarding.EmployeeTasks et
                  WHERE et.EmployeeId = e.EmployeeId AND et.TaskId = t.TaskId);
        """
        read = """
            SELECT et.EmployeeTaskId AS employee_task_id, et.TaskId AS task_id,
                   t.Title AS title, t.Description AS description, t.Phase AS phase,
                   t.Category AS category, t.IsRequired AS is_required,
                   et.Status AS status, et.DueDate AS due_date,
                   et.CompletedAt AS completed_at
            FROM Onboarding.EmployeeTasks et
            JOIN Onboarding.Tasks t ON t.TaskId = et.TaskId
            WHERE et.EmployeeId = ?
            ORDER BY t.SortOrder;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM Core.Employees WHERE EmployeeId = ?;", employee_id)
            if cur.fetchone() is None:
                raise NotFoundError(f"Employee {employee_id} not found")
            cur.execute(assign, employee_id)
            cur.execute(read, employee_id)
            return self._rows_as_dicts(cur)

    def update_task(self, employee_task_id: int, status: str, notes: str | None) -> dict:
        sql = """
            UPDATE Onboarding.EmployeeTasks
            SET Status = ?,
                CompletedAt = CASE WHEN ? = 'Completed' THEN SYSUTCDATETIME() ELSE NULL END,
                Notes = COALESCE(?, Notes),
                UpdatedAt = SYSUTCDATETIME()
            OUTPUT INSERTED.EmployeeTaskId AS employee_task_id, INSERTED.TaskId AS task_id,
                   INSERTED.Status AS status, INSERTED.DueDate AS due_date,
                   INSERTED.CompletedAt AS completed_at
            WHERE EmployeeTaskId = ?;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, status, status, notes, employee_task_id)
            rows = self._rows_as_dicts(cur)
            conn.commit()
        if not rows:
            raise NotFoundError(f"Task {employee_task_id} not found")
        return rows[0]

    # --- Documents --------------------------------------------------------
    def add_document(self, employee_id: int, record: dict) -> dict:
        sql = """
            INSERT INTO Storage.EmployeeDocuments
                (EmployeeId, DocumentType, OriginalFileName, ContainerName,
                 BlobUri, ContentType, SizeBytes)
            OUTPUT INSERTED.DocumentId AS document_id, INSERTED.EmployeeId AS employee_id,
                   INSERTED.DocumentType AS document_type,
                   INSERTED.OriginalFileName AS original_file_name,
                   INSERTED.ContainerName AS container_name, INSERTED.BlobUri AS blob_uri,
                   INSERTED.ContentType AS content_type, INSERTED.SizeBytes AS size_bytes,
                   INSERTED.UploadedAt AS uploaded_at
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                sql,
                employee_id,
                record["document_type"],
                record["original_file_name"],
                record["container_name"],
                record["blob_uri"],
                record.get("content_type"),
                record.get("size_bytes"),
            )
            rows = self._rows_as_dicts(cur)
            conn.commit()
        return rows[0]

    def list_documents(self, employee_id: int) -> list[dict]:
        sql = """
            SELECT DocumentId AS document_id, EmployeeId AS employee_id,
                   DocumentType AS document_type, OriginalFileName AS original_file_name,
                   ContainerName AS container_name, BlobUri AS blob_uri,
                   ContentType AS content_type, SizeBytes AS size_bytes,
                   UploadedAt AS uploaded_at
            FROM Storage.EmployeeDocuments
            WHERE EmployeeId = ? AND IsDeleted = 0
            ORDER BY DocumentId;
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, employee_id)
            return self._rows_as_dicts(cur)

    # --- Chat -------------------------------------------------------------
    def save_message(self, employee_id: int, role: str, content: str) -> None:
        # A single-turn helper; conversation grouping uses a per-request GUID
        # generated by the chat service.
        sql = """
            INSERT INTO Chat.ChatHistory (ConversationId, EmployeeId, Role, Content)
            VALUES (NEWID(), ?, ?, ?);
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, employee_id, role, content)
            conn.commit()


__all__ = ["SqlRepository"]
