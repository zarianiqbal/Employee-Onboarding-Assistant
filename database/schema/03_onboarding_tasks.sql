-- =============================================================================
-- 03_onboarding_tasks.sql
-- Onboarding.Tasks: the master catalog of onboarding tasks.
--
-- A reference table of every possible onboarding task across the organization,
-- categorized by phase (Pre-boarding, Day 1, Week 1, ...). Employee-specific
-- progress lives in Onboarding.EmployeeTasks (the junction table).
-- =============================================================================

IF OBJECT_ID('Onboarding.Tasks', 'U') IS NOT NULL
    DROP TABLE Onboarding.Tasks;
GO

CREATE TABLE Onboarding.Tasks
(
    TaskId          INT             IDENTITY(1,1) NOT NULL,
    Title           NVARCHAR(200)   NOT NULL,
    Description     NVARCHAR(1000)  NULL,
    Phase           NVARCHAR(40)    NOT NULL,       -- Pre-boarding / Day 1 / Week 1 ...
    Category        NVARCHAR(60)    NULL,           -- HR / IT / Compliance ...
    -- Days from the employee's start date this task is due (can be negative
    -- for pre-boarding tasks that must be done before Day 1).
    DueOffsetDays   INT             NOT NULL
        CONSTRAINT DF_Tasks_DueOffsetDays DEFAULT (0),
    IsRequired      BIT             NOT NULL
        CONSTRAINT DF_Tasks_IsRequired DEFAULT (1),
    SortOrder       INT             NOT NULL
        CONSTRAINT DF_Tasks_SortOrder DEFAULT (100),
    IsActive        BIT             NOT NULL
        CONSTRAINT DF_Tasks_IsActive DEFAULT (1),
    CreatedAt       DATETIME2(3)    NOT NULL
        CONSTRAINT DF_Tasks_CreatedAt DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_Tasks PRIMARY KEY CLUSTERED (TaskId),
    CONSTRAINT CK_Tasks_Phase
        CHECK (Phase IN ('Pre-boarding', 'Day 1', 'Week 1', 'Week 2', 'Month 1'))
);
GO

CREATE INDEX IX_Tasks_Phase ON Onboarding.Tasks (Phase, SortOrder);
GO
