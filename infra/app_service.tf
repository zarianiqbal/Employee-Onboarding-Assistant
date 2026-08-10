# Azure App Service (Linux) hosting the FastAPI backend.
#
# A system-assigned managed identity is enabled so the app authenticates to
# SQL, Storage, OpenAI, and AI Search with Entra tokens — no secrets in config.
# App settings reference resource endpoints (not keys); the identity does the
# rest at runtime via DefaultAzureCredential.

resource "azurerm_service_plan" "main" {
  name                = "asp-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.environment == "prod" ? "P1v3" : "B1"
  tags                = var.tags
}

resource "azurerm_linux_web_app" "backend" {
  name                = "app-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on = var.environment == "prod"
    application_stack {
      python_version = "3.12"
    }
    # Gunicorn + Uvicorn workers for the async FastAPI app.
    app_command_line = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app"
  }

  app_settings = {
    # Endpoints only — authentication is via managed identity, not keys.
    "AZURE_SQL_SERVER"                      = azurerm_mssql_server.main.fully_qualified_domain_name
    "AZURE_SQL_DATABASE"                    = azurerm_mssql_database.main.name
    "AZURE_STORAGE_ACCOUNT_URL"             = azurerm_storage_account.main.primary_blob_endpoint
    "POLICIES_CONTAINER"                    = azurerm_storage_container.policies.name
    "DOCUMENTS_CONTAINER"                   = azurerm_storage_container.documents.name
    "AZURE_OPENAI_ENDPOINT"                 = azurerm_cognitive_account.openai.endpoint
    "AZURE_SEARCH_ENDPOINT"                 = "https://${azurerm_search_service.main.name}.search.windows.net"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "true"
  }

  tags = var.tags
}
