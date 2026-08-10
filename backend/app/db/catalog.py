"""The standard onboarding task catalog.

Mirrors database/seed/01_task_catalog.sql so the in-memory repository (local
mode) behaves like the seeded Azure SQL database. Each tuple is:
(task_id, title, description, phase, category, due_offset_days, is_required, sort_order)
"""
from __future__ import annotations

TASK_CATALOG: list[dict] = [
    # Pre-boarding
    {"task_id": 1, "title": "Accept your onboarding invitation", "description": "Redeem the email invite and sign in with your account.", "phase": "Pre-boarding", "category": "HR", "due_offset_days": -3, "is_required": True, "sort_order": 10},
    {"task_id": 2, "title": "Sign your offer letter", "description": "Review and e-sign your offer letter.", "phase": "Pre-boarding", "category": "HR", "due_offset_days": -3, "is_required": True, "sort_order": 20},
    {"task_id": 3, "title": "Submit government-issued ID", "description": "Upload a photo of your passport or driver's license.", "phase": "Pre-boarding", "category": "Compliance", "due_offset_days": -1, "is_required": True, "sort_order": 30},
    # Day 1
    {"task_id": 4, "title": "Complete tax forms (W-4 / equivalent)", "description": "Fill out and submit required tax withholding forms.", "phase": "Day 1", "category": "Compliance", "due_offset_days": 0, "is_required": True, "sort_order": 40},
    {"task_id": 5, "title": "Set up your work account & MFA", "description": "Activate your work email and enable multi-factor auth.", "phase": "Day 1", "category": "IT", "due_offset_days": 0, "is_required": True, "sort_order": 50},
    {"task_id": 6, "title": "Read the code of conduct", "description": "Review and acknowledge the company code of conduct.", "phase": "Day 1", "category": "Compliance", "due_offset_days": 0, "is_required": True, "sort_order": 60},
    {"task_id": 7, "title": "Meet your onboarding buddy", "description": "Introductory chat with your assigned onboarding buddy.", "phase": "Day 1", "category": "HR", "due_offset_days": 0, "is_required": False, "sort_order": 70},
    # Week 1
    {"task_id": 8, "title": "Complete security awareness training", "description": "Finish the required security awareness course.", "phase": "Week 1", "category": "Compliance", "due_offset_days": 5, "is_required": True, "sort_order": 80},
    {"task_id": 9, "title": "Enroll in benefits", "description": "Select your health, retirement, and other benefits.", "phase": "Week 1", "category": "HR", "due_offset_days": 5, "is_required": True, "sort_order": 90},
    {"task_id": 10, "title": "Add emergency contact information", "description": "Provide an emergency contact in your profile.", "phase": "Week 1", "category": "HR", "due_offset_days": 5, "is_required": False, "sort_order": 100},
    # Week 2
    {"task_id": 11, "title": "1:1 with your manager", "description": "Schedule and hold your first 1:1 with your manager.", "phase": "Week 2", "category": "HR", "due_offset_days": 10, "is_required": False, "sort_order": 110},
    {"task_id": 12, "title": "Complete role-specific training", "description": "Finish the training modules assigned for your role.", "phase": "Week 2", "category": "IT", "due_offset_days": 10, "is_required": True, "sort_order": 120},
    # Month 1
    {"task_id": 13, "title": "30-day onboarding check-in", "description": "Reflect on your first month and share feedback with HR.", "phase": "Month 1", "category": "HR", "due_offset_days": 30, "is_required": False, "sort_order": 130},
]
