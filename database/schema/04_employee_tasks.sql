-- =============================================================================
-- 04_employee_tasks.sql
-- Onboarding.EmployeeTasks: the progression tracker (junction table).
--
-- Maps an employee to their specific onboarding tasks and tracks status. This
-- powers the React checklist dashboard and provides structured context to the
-- AI chatbot (what is pending / completed for this user).
-- =============================================================================

IF OBJECT_ID('Onboarding.EmployeeTasks', 'U') IS NOT NULL
    DROP TABLE Onboarding.EmployeeTasks;
GO

CREATE TABLE Onboarding.EmployeeTasks
(
    EmployeeTaskId  INT             IDENTITY(1,1) NOT NULL,
    EmployeeId      INT             NOT NULL,
    TaskId          INT             NOT NULL,
    Status          NVARCHAR(20)    NOT NULL
        CONSTRAINT DF_EmployeeTasks_Status DEFAULT ('Pending'),
    DueDate         DATE            NULL,           -- computed from StartDate + offset
    CompletedAt     DATETIME2(3)    NULL,
    Notes           NVARCHAR(1000)  NULL,
    CreatedAt       DATETIME2(3)    NOT NULL
        CONSTRAINT DF_EmployeeTasks_CreatedAt DEFAULT (SYSUTCDATETIME()),
    UpdatedAt       DATETIME2(3)    NOT NULL
        CONSTRAINT DF_EmployeeTasks_UpdatedAt DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_EmployeeTasks PRIMARY KEY CLUSTERED (EmployeeTaskId),
    CONSTRAINT CK_EmployeeTasks_Status
        CHECK (Status IN ('Pending', 'InProgress', 'Completed', 'Skipped')),
    CONSTRAINT FK_EmployeeTasks_Employee
        FOREIGN KEY (EmployeeId) REFERENCES Core.Employees(EmployeeId),
    CONSTRAINT FK_EmployeeTasks_Task
        FOREIGN KEY (TaskId) REFERENCES Onboarding.Tasks(TaskId),
    -- An employee is assigned any given task at most once.
    CONSTRAINT UQ_EmployeeTasks_Employee_Task UNIQUE (EmployeeId, TaskId)
);
GO

-- Read-heavy: the dashboard fetches all tasks for one employee constantly.
-- Highly indexed so the checklist and chatbot context reads are millisecond-fast.
CREATE INDEX IX_EmployeeTasks_Employee
    ON Onboarding.EmployeeTasks (EmployeeId)
    INCLUDE (TaskId, Status, DueDate, CompletedAt);
GO
