-- =============================================================================
-- 02_core_employees.sql
-- Core.Employees: the central new-hire profile.
--
-- This table captures the initial data HR provides to trigger the Microsoft
-- Graph B2B invitation, then progressively fills in as the employee onboards.
-- Secondary fields are nullable to support progressive profiling: the user is
-- never blocked from creating an account because a field is missing.
--
-- AI-context columns (Department, ClearanceLevel, Region) let the RAG pipeline
-- apply metadata filtering so, e.g., a UK employee doesn't receive answers
-- based on US-only policies.
-- =============================================================================

IF OBJECT_ID('Core.Employees', 'U') IS NOT NULL
    DROP TABLE Core.Employees;
GO

CREATE TABLE Core.Employees
(
    EmployeeId              INT             IDENTITY(1,1) NOT NULL,
    -- Identity / invitation (Microsoft Graph B2B)
    EntraObjectId           NVARCHAR(100)   NULL,           -- set after redemption
    FirstName               NVARCHAR(100)   NOT NULL,
    LastName                NVARCHAR(100)   NOT NULL,
    PersonalEmail           NVARCHAR(256)   NOT NULL,        -- invite target
    WorkEmail               NVARCHAR(256)   NULL,
    InvitationStatus        NVARCHAR(30)    NOT NULL
        CONSTRAINT DF_Employees_InvitationStatus DEFAULT ('PendingAcceptance'),
    ExternalUserStateChangeDateTime DATETIME2(3) NULL,

    -- Job information
    JobTitle                NVARCHAR(150)   NULL,
    Department              NVARCHAR(100)   NULL,            -- AI metadata filter
    Region                  NVARCHAR(60)    NULL,            -- AI metadata filter
    ClearanceLevel          NVARCHAR(40)    NULL,            -- AI metadata filter
    ManagerEmployeeId       INT             NULL,
    StartDate               DATE            NULL,

    -- Progressive-profiling fields (collected later, nullable by design)
    DateOfBirth             DATE            NULL,
    PhoneNumber             NVARCHAR(30)    NULL,
    HomeAddress             NVARCHAR(400)   NULL,

    -- Auditing
    IsActive                BIT             NOT NULL
        CONSTRAINT DF_Employees_IsActive DEFAULT (1),
    CreatedAt               DATETIME2(3)    NOT NULL
        CONSTRAINT DF_Employees_CreatedAt DEFAULT (SYSUTCDATETIME()),
    UpdatedAt               DATETIME2(3)    NOT NULL
        CONSTRAINT DF_Employees_UpdatedAt DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_Employees PRIMARY KEY CLUSTERED (EmployeeId),
    CONSTRAINT CK_Employees_InvitationStatus
        CHECK (InvitationStatus IN ('PendingAcceptance', 'Accepted', 'Revoked')),
    CONSTRAINT FK_Employees_Manager
        FOREIGN KEY (ManagerEmployeeId) REFERENCES Core.Employees(EmployeeId)
);
GO

-- Personal email is the invite key; enforce uniqueness among active records.
CREATE UNIQUE INDEX UX_Employees_PersonalEmail
    ON Core.Employees (PersonalEmail)
    WHERE IsActive = 1;
GO

-- Fast lookup by Entra object id after the user authenticates.
CREATE INDEX IX_Employees_EntraObjectId
    ON Core.Employees (EntraObjectId)
    WHERE EntraObjectId IS NOT NULL;
GO

-- Supports AI metadata filtering by department/region.
CREATE INDEX IX_Employees_DeptRegion
    ON Core.Employees (Department, Region);
GO
