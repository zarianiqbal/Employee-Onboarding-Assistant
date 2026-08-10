"""Microsoft Graph B2B invitation flow.

When HR registers a new hire, the backend calls the Microsoft Graph
`/invitations` endpoint (authenticated with the App Service managed identity) to
send a secure, one-time redemption link to the new hire's personal email. Entra
supports Google/Microsoft account federation, so the user signs in with their
existing personal account and is redirected back to the app with a verified JWT.

In local mode (no Entra tenant configured) a stub redemption URL is returned so
the flow can be demonstrated without a real directory.
"""
from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_GRAPH_INVITATIONS_URL = "https://graph.microsoft.com/v1.0/invitations"
_GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def send_invitation(employee: dict) -> dict:
    """Send a B2B invite to the employee's personal email.

    Returns a dict with the redemption URL and the invitation status.
    """
    settings = get_settings()
    display_name = f"{employee['first_name']} {employee['last_name']}"
    email = employee["personal_email"]

    if not settings.entra_configured:
        logger.warning("Entra not configured — returning stub invitation for %s", email)
        return {
            "invited_email": email,
            "redeem_url": f"{settings.invite_redirect_url}?stub_invite=1",
            "status": "PendingAcceptance",
            "stub": True,
        }

    import httpx

    from app.core.azure_clients import get_credential

    token = get_credential().get_token(_GRAPH_SCOPE).token
    payload = {
        "invitedUserEmailAddress": email,
        "invitedUserDisplayName": display_name,
        "inviteRedirectUrl": settings.invite_redirect_url,
        "sendInvitationMessage": True,
    }
    resp = httpx.post(
        _GRAPH_INVITATIONS_URL,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    return {
        "invited_email": email,
        "redeem_url": body.get("inviteRedeemUrl", ""),
        "status": body.get("status", "PendingAcceptance"),
        "invited_user_object_id": body.get("invitedUser", {}).get("id"),
        "stub": False,
    }
