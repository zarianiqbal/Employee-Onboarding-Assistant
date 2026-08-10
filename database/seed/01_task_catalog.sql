-- =============================================================================
-- 01_task_catalog.sql
-- Seed the standard onboarding task catalog (Onboarding.Tasks).
-- Idempotent: only inserts tasks that are not already present (matched by Title).
-- =============================================================================

MERGE Onboarding.Tasks AS target
USING (VALUES
    -- Pre-boarding
    (N'Accept your onboarding invitation',        N'Redeem the email invite and sign in with your account.', N'Pre-boarding', N'HR',         -3, 1, 10),
    (N'Sign your offer letter',                   N'Review and e-sign your offer letter.',                    N'Pre-boarding', N'HR',         -3, 1, 20),
    (N'Submit government-issued ID',              N'Upload a photo of your passport or driver''s license.',    N'Pre-boarding', N'Compliance', -1, 1, 30),
    -- Day 1
    (N'Complete tax forms (W-4 / equivalent)',    N'Fill out and submit required tax withholding forms.',     N'Day 1',        N'Compliance',  0, 1, 40),
    (N'Set up your work account & MFA',           N'Activate your work email and enable multi-factor auth.',  N'Day 1',        N'IT',          0, 1, 50),
    (N'Read the code of conduct',                 N'Review and acknowledge the company code of conduct.',      N'Day 1',        N'Compliance',  0, 1, 60),
    (N'Meet your onboarding buddy',               N'Introductory chat with your assigned onboarding buddy.',   N'Day 1',        N'HR',          0, 0, 70),
    -- Week 1
    (N'Complete security awareness training',     N'Finish the required security awareness course.',           N'Week 1',       N'Compliance',  5, 1, 80),
    (N'Enroll in benefits',                       N'Select your health, retirement, and other benefits.',      N'Week 1',       N'HR',          5, 1, 90),
    (N'Add emergency contact information',        N'Provide an emergency contact in your profile.',            N'Week 1',       N'HR',          5, 0, 100),
    -- Week 2
    (N'1:1 with your manager',                    N'Schedule and hold your first 1:1 with your manager.',      N'Week 2',       N'HR',         10, 0, 110),
    (N'Complete role-specific training',          N'Finish the training modules assigned for your role.',      N'Week 2',       N'IT',         10, 1, 120),
    -- Month 1
    (N'30-day onboarding check-in',               N'Reflect on your first month and share feedback with HR.',  N'Month 1',      N'HR',         30, 0, 130)
) AS source (Title, Description, Phase, Category, DueOffsetDays, IsRequired, SortOrder)
ON target.Title = source.Title
WHEN NOT MATCHED BY TARGET THEN
    INSERT (Title, Description, Phase, Category, DueOffsetDays, IsRequired, SortOrder)
    VALUES (source.Title, source.Description, source.Phase, source.Category,
            source.DueOffsetDays, source.IsRequired, source.SortOrder);
GO
