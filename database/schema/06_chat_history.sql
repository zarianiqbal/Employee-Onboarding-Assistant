-- =============================================================================
-- 06_chat_history.sql
-- Chat.ChatHistory: conversation persistence for the AI assistant.
--
-- Rather than standing up a separate Cosmos DB / PostgreSQL just for chat
-- history (as the "chat-with-your-data" accelerator defaults to), we keep one
-- database technology and store conversation turns here. This lets a new hire
-- pick up their onboarding research across multiple sessions.
-- =============================================================================

IF OBJECT_ID('Chat.ChatHistory', 'U') IS NOT NULL
    DROP TABLE Chat.ChatHistory;
GO

CREATE TABLE Chat.ChatHistory
(
    MessageId       BIGINT          IDENTITY(1,1) NOT NULL,
    ConversationId  UNIQUEIDENTIFIER NOT NULL,
    EmployeeId      INT             NOT NULL,
    Role            NVARCHAR(20)    NOT NULL,       -- user / assistant / system
    Content         NVARCHAR(MAX)   NOT NULL,
    -- Optional citations (JSON array of source doc references from RAG).
    Citations       NVARCHAR(MAX)   NULL,
    TokenCount      INT             NULL,
    CreatedAt       DATETIME2(3)    NOT NULL
        CONSTRAINT DF_ChatHistory_CreatedAt DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_ChatHistory PRIMARY KEY CLUSTERED (MessageId),
    CONSTRAINT CK_ChatHistory_Role
        CHECK (Role IN ('user', 'assistant', 'system')),
    CONSTRAINT FK_ChatHistory_Employee
        FOREIGN KEY (EmployeeId) REFERENCES Core.Employees(EmployeeId)
);
GO

-- Fetch a full conversation in order.
CREATE INDEX IX_ChatHistory_Conversation
    ON Chat.ChatHistory (ConversationId, CreatedAt);
GO
