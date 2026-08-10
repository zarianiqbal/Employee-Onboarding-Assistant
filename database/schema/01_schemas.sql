-- =============================================================================
-- 01_schemas.sql
-- Create the logical schemas used to organize onboarding data.
-- Schemas keep concerns separated: employee profiles (Core), onboarding
-- workflow (Onboarding), blob references (Storage), and chat history (Chat).
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'Core')
    EXEC('CREATE SCHEMA Core');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'Onboarding')
    EXEC('CREATE SCHEMA Onboarding');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'Storage')
    EXEC('CREATE SCHEMA Storage');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'Chat')
    EXEC('CREATE SCHEMA Chat');
GO
