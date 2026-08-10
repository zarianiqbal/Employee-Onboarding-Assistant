"""Entra ID JWT validation.

After the new hire authenticates via SSO, the frontend sends the resulting JWT
to the backend. `verify_token` validates it against the tenant's published JWKS
(signature, issuer, audience, expiry) and returns the decoded claims.

When no tenant is configured (local mode) validation is skipped and an optional
`X-Debug-Object-Id` header stands in for the verified identity, so the flow can
be exercised end-to-end without a directory. This permissive path is only ever
taken when `entra_configured` is False.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Header, HTTPException

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Principal:
    """The authenticated caller derived from a validated token."""

    object_id: str
    email: str | None = None


@lru_cache
def _jwks_client():
    from jwt import PyJWKClient  # lazy import

    settings = get_settings()
    url = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/discovery/v2.0/keys"
    return PyJWKClient(url)


def verify_token(
    authorization: str | None = Header(default=None),
    x_debug_object_id: str | None = Header(default=None),
) -> Principal:
    """FastAPI dependency that returns the verified caller identity."""
    settings = get_settings()

    if not settings.entra_configured:
        # Local mode: accept a debug header as the stand-in identity.
        return Principal(object_id=x_debug_object_id or "local-dev-user")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    import jwt  # lazy import

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.api_audience,
            issuer=f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
        )
    except jwt.PyJWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    object_id = claims.get("oid") or claims.get("sub")
    if not object_id:
        raise HTTPException(status_code=401, detail="Token missing subject")
    email = claims.get("preferred_username") or claims.get("email")
    return Principal(object_id=object_id, email=email)
