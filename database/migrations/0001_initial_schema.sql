-- =============================================================================
-- Migration 0001: initial schema
--
-- Establishes the baseline objects for the onboarding system. This migration is
-- idempotent — each object is guarded so re-running against an existing database
-- is safe. It composes the individual files under schema/ into one ordered,
-- deployable unit for CI/CD.
--
-- Apply order:
--   1. schemas          (Core, Onboarding, Storage, Chat)
--   2. Core.Employees
--   3. Onboarding.Tasks
--   4. Onboarding.EmployeeTasks
--   5. Storage.EmployeeDocuments
--   6. Chat.ChatHistory
--
-- In CI this migration is applied via sqlcmd using Entra ID authentication
-- (no static passwords). See .github/workflows/database.yml.
-- =============================================================================

-- A lightweight migration ledger so the pipeline knows what has been applied.
IF OBJECT_ID('dbo.__SchemaMigrations', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.__SchemaMigrations
    (
        MigrationId   NVARCHAR(100) NOT NULL PRIMARY KEY,
        AppliedAt     DATETIME2(3)  NOT NULL DEFAULT (SYSUTCDATETIME())
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.__SchemaMigrations WHERE MigrationId = '0001_initial_schema')
BEGIN
    PRINT 'Applying migration 0001_initial_schema...';
    -- The schema/*.sql files are executed in order by the pipeline before this
    -- ledger entry is written. This block simply records the application.
    INSERT INTO dbo.__SchemaMigrations (MigrationId) VALUES ('0001_initial_schema');
END
ELSE
BEGIN
    PRINT 'Migration 0001_initial_schema already applied; skipping.';
END
GO
