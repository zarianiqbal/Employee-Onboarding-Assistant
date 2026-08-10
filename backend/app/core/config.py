"""Application configuration.

Settings are read from environment variables (or a local `.env`). Notably there
are no secrets here — only resource *endpoints*. Authentication to Azure uses
managed identity in the cloud and the developer's `az login` locally, both via
`DefaultAzureCredential`.

When an Azure endpoint is left blank the app runs in a degraded "local" mode
(in-memory store, stubbed AI) so the frontend and tests can run without a cloud
subscription.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    # Microsoft Entra ID (B2B invitations + JWT validation)
    azure_tenant_id: str = ""
    api_audience: str = ""  # this API's app (client) id; the expected JWT audience
    invite_redirect_url: str = "http://localhost:5173/register"

    # Azure SQL
    azure_sql_server: str = ""
    azure_sql_database: str = ""

    # Azure Blob Storage
    azure_storage_account_url: str = ""
    policies_container: str = "company-policies"
    documents_container: str = "employee-documents"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_chat_deployment: str = "chat"
    azure_openai_embedding_deployment: str = "embeddings"
    azure_openai_api_version: str = "2024-10-21"

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_index: str = "onboarding-policies"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sql_configured(self) -> bool:
        return bool(self.azure_sql_server and self.azure_sql_database)

    @property
    def entra_configured(self) -> bool:
        return bool(self.azure_tenant_id and self.api_audience)

    @property
    def storage_configured(self) -> bool:
        return bool(self.azure_storage_account_url)

    @property
    def openai_configured(self) -> bool:
        return bool(self.azure_openai_endpoint)

    @property
    def search_configured(self) -> bool:
        return bool(self.azure_search_endpoint)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
