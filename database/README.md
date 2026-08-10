# Database

Azure SQL Database schema for the Employee Onboarding Assistant. All objects are
defined in versioned T-SQL so changes flow through Git → PR review → CI/CD →
Azure, never manual portal edits.

## Layout

```
database/
├── schema/       # Table definitions (run in numeric order)
│   ├── 01_schemas.sql
│   ├── 02_core_employees.sql
│   ├── 03_onboarding_tasks.sql
│   ├── 04_employee_tasks.sql
│   ├── 05_employee_documents.sql
│   └── 06_chat_history.sql
├── migrations/   # Ordered, idempotent change scripts
└── seed/         # Reference data + mock-data generation
```

## Entities

| Table                        | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| `Core.Employees`             | Central new-hire profile (B2B invite + profiling)    |
| `Onboarding.Tasks`           | Master catalog of onboarding tasks, by phase         |
| `Onboarding.EmployeeTasks`   | Per-employee task progress (junction table)          |
| `Storage.EmployeeDocuments`  | Blob references (URI, version, soft-delete)          |
| `Chat.ChatHistory`           | AI assistant conversation history                    |

## Applying the schema locally

Against a local SQL Server / Azure SQL instance with `sqlcmd`:

```bash
for f in schema/*.sql; do
  sqlcmd -S "$SQL_SERVER" -d "$SQL_DATABASE" -G -i "$f"
done
```

`-G` uses Entra ID (Azure AD) auth — no static password. In CI, connection is
made through a managed identity / service principal, never a hardcoded string.

## Migrations

Migration scripts in `migrations/` are:

- **Ordered** — prefixed with a zero-padded sequence number.
- **Idempotent** — guarded with `IF NOT EXISTS` so re-runs are safe.

## Seeding

`seed/01_task_catalog.sql` loads the standard onboarding task catalog.
`seed/generate_mock_employees.py` uses [Faker](https://faker.readthedocs.io/) to
produce realistic mock employees + task assignments for Dev/Staging — never
Production.
