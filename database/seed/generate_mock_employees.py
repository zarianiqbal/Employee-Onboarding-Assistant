#!/usr/bin/env python3
"""Generate a T-SQL seed file of realistic mock employees + task assignments.

Uses the Faker library to programmatically produce localized names, job titles,
start dates, and contact details, then emits batched INSERT statements. The
output is intended to be run against Dev/Staging Azure SQL only (never Prod) as
part of the CI/CD pipeline.

Usage:
    python generate_mock_employees.py --count 250 --out mock_employees.sql
"""
from __future__ import annotations

import argparse
import random
from datetime import date, timedelta

try:
    from faker import Faker
except ImportError as exc:  # pragma: no cover - helpful error for first run
    raise SystemExit(
        "The 'faker' package is required. Install it with: pip install faker"
    ) from exc

DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Finance",
    "People Ops", "Customer Success", "Legal", "IT",
]
REGIONS = ["US", "UK", "EU", "APAC", "LATAM"]
CLEARANCE_LEVELS = ["Standard", "Elevated", "Restricted"]
INVITATION_STATUSES = ["PendingAcceptance", "Accepted"]


def sql_escape(value: str) -> str:
    """Escape single quotes for safe inline T-SQL string literals."""
    return value.replace("'", "''")


def build_employee_rows(count: int, seed: int) -> list[str]:
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    rows: list[str] = []
    for _ in range(count):
        first = fake.first_name()
        last = fake.last_name()
        personal_email = f"{first}.{last}.{random.randint(1, 9999)}@example.com".lower()
        job = fake.job()[:150]
        dept = random.choice(DEPARTMENTS)
        region = random.choice(REGIONS)
        clearance = random.choice(CLEARANCE_LEVELS)
        status = random.choice(INVITATION_STATUSES)
        start = date.today() + timedelta(days=random.randint(-30, 30))
        phone = fake.phone_number()[:30]

        rows.append(
            "(N'{first}', N'{last}', N'{email}', N'{status}', N'{job}', "
            "N'{dept}', N'{region}', N'{clearance}', '{start}', N'{phone}')".format(
                first=sql_escape(first),
                last=sql_escape(last),
                email=sql_escape(personal_email),
                status=status,
                job=sql_escape(job),
                dept=dept,
                region=region,
                clearance=clearance,
                start=start.isoformat(),
                phone=sql_escape(phone),
            )
        )
    return rows


def render_sql(rows: list[str]) -> str:
    header = (
        "-- Auto-generated mock employees. DO NOT run against Production.\n"
        "-- Regenerate with: python generate_mock_employees.py\n"
        "SET NOCOUNT ON;\n\n"
    )

    # Batch inserts in groups of 100 (T-SQL caps table value constructors at 1000).
    body_parts: list[str] = []
    batch_size = 100
    columns = (
        "INSERT INTO Core.Employees\n"
        "    (FirstName, LastName, PersonalEmail, InvitationStatus, JobTitle,\n"
        "     Department, Region, ClearanceLevel, StartDate, PhoneNumber)\nVALUES\n"
    )
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        body_parts.append(columns + ",\n".join(batch) + ";\nGO\n")

    # Assign every employee the full active task catalog (Pending status),
    # with a DueDate computed from their StartDate + the task's offset.
    assignment = (
        "\n-- Assign the active task catalog to every seeded employee.\n"
        "INSERT INTO Onboarding.EmployeeTasks (EmployeeId, TaskId, Status, DueDate)\n"
        "SELECT e.EmployeeId, t.TaskId, 'Pending',\n"
        "       DATEADD(DAY, t.DueOffsetDays, e.StartDate)\n"
        "FROM Core.Employees e\n"
        "CROSS JOIN Onboarding.Tasks t\n"
        "WHERE t.IsActive = 1\n"
        "  AND NOT EXISTS (\n"
        "      SELECT 1 FROM Onboarding.EmployeeTasks et\n"
        "      WHERE et.EmployeeId = e.EmployeeId AND et.TaskId = t.TaskId\n"
        "  );\nGO\n"
    )

    return header + "".join(body_parts) + assignment


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock employee seed SQL.")
    parser.add_argument("--count", type=int, default=250, help="number of employees")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    parser.add_argument("--out", default="mock_employees.sql", help="output .sql path")
    args = parser.parse_args()

    rows = build_employee_rows(args.count, args.seed)
    sql = render_sql(rows)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(sql)
    print(f"Wrote {args.count} mock employees to {args.out}")


if __name__ == "__main__":
    main()
