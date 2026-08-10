"""FastAPI application entrypoint.

Wires up logging, CORS, and the versioned API router. A lifespan handler logs
which Azure integrations are active vs. running in local/stub mode.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Onboarding Assistant backend v%s (env=%s)", __version__, settings.app_env)
    logger.info(
        "Integrations — SQL:%s Storage:%s OpenAI:%s Search:%s",
        settings.sql_configured,
        settings.storage_configured,
        settings.openai_configured,
        settings.search_configured,
    )
    yield
    logger.info("Shutting down backend")


app = FastAPI(
    title="Employee Onboarding Assistant API",
    version=__version__,
    description="REST API for new-hire registration, tasks, documents, and the AI assistant.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["meta"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Simple liveness check for load balancers / App Service health probes."""
    return {"status": "ok", "version": __version__}


@app.get("/ready", tags=["meta"], summary="Readiness probe")
async def ready() -> dict[str, object]:
    """Readiness check reporting which backing integrations are configured."""
    return {
        "status": "ready",
        "integrations": {
            "sql": settings.sql_configured,
            "storage": settings.storage_configured,
            "openai": settings.openai_configured,
            "search": settings.search_configured,
        },
    }
