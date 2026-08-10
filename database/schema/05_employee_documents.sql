-- =============================================================================
-- 05_employee_documents.sql
-- Storage.EmployeeDocuments: blob references.
--
-- Files themselves live in Azure Blob Storage (uploaded directly from the
-- browser via SAS tokens). The database only stores secure references: the
-- blob URI, a version id, soft-delete flags, and any metadata extracted from
-- the document (e.g. via Azure AI Document Intelligence).
-- =============================================================================

IF OBJECT_ID('Storage.EmployeeDocuments', 'U') IS NOT NULL
    DROP TABLE Storage.EmployeeDocuments;
GO

CREATE TABLE Storage.EmployeeDocuments
(
    DocumentId          INT             IDENTITY(1,1) NOT NULL,
    EmployeeId          INT             NOT NULL,
    DocumentType        NVARCHAR(60)    NOT NULL,       -- ID / TaxForm / Certificate ...
    OriginalFileName    NVARCHAR(400)   NOT NULL,
    ContainerName       NVARCHAR(100)   NOT NULL,       -- e.g. employee-documents
    BlobUri             NVARCHAR(1000)  NOT NULL,
    BlobVersionId       NVARCHAR(100)   NULL,           -- blob versioning id
    ContentType         NVARCHAR(120)   NULL,
    SizeBytes           BIGINT          NULL,
    -- Raw JSON from Azure AI Document Intelligence (OCR extraction).
    ExtractedMetadata   NVARCHAR(MAX)   NULL,
    IsDeleted           BIT             NOT NULL         -- soft delete
        CONSTRAINT DF_Documents_IsDeleted DEFAULT (0),
    UploadedAt          DATETIME2(3)    NOT NULL
        CONSTRAINT DF_Documents_UploadedAt DEFAULT (SYSUTCDATETIME()),
    LastModified        DATETIME2(3)    NOT NULL
        CONSTRAINT DF_Documents_LastModified DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_Documents PRIMARY KEY CLUSTERED (DocumentId),
    CONSTRAINT FK_Documents_Employee
        FOREIGN KEY (EmployeeId) REFERENCES Core.Employees(EmployeeId)
);
GO

CREATE INDEX IX_Documents_Employee
    ON Storage.EmployeeDocuments (EmployeeId)
    WHERE IsDeleted = 0;
GO
