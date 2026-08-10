"""Repository factory: pick SQL-backed or in-memory based on configuration."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import get_settings
from app.db.repository import InMemoryRepository, Repository

logger = logging.getLogger(__name__)


@lru_cache
def get_repository() -> Repository:
    """Return the process-wide repository singleton.

    Uses Azure SQL when configured; otherwise falls back to an in-memory store
    (local development and tests).
    """
    settings = get_settings()
    if settings.sql_configured:
        from app.db.sql_repository import SqlRepository

        logger.info("Using SQL repository (server=%s)", settings.azure_sql_server)
        return SqlRepository()

    logger.warning("Azure SQL not configured — using in-memory repository (local mode)")
    return InMemoryRepository()
