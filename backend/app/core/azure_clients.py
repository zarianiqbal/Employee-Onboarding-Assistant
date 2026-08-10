"""Azure credential + client helpers (secretless).

Every Azure client authenticates with `DefaultAzureCredential`, which resolves
to the App Service managed identity in Azure and to the developer's `az login`
session locally. No connection strings, account keys, or API keys are used.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid importing heavy SDKs at module load / in local mode
    from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


@lru_cache
def get_credential() -> DefaultAzureCredential:
    """Return a cached DefaultAzureCredential.

    Imported lazily so the app can run in local mode without azure-identity
    installed or an Azure session available.
    """
    from azure.identity import DefaultAzureCredential

    logger.info("Initializing DefaultAzureCredential (managed identity / az login)")
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)
