# RBAC role assignments (secretless security).
#
# Grant the App Service managed identity least-privilege access to each data/AI
# service. These assignments replace connection-string secrets entirely: the
# backend requests short-lived Entra tokens at runtime.

locals {
  backend_principal_id = azurerm_linux_web_app.backend.identity[0].principal_id
}

# --- Blob Storage ---------------------------------------------------------
# Backend needs to read/write documents and mint user-delegation SAS tokens,
# which requires the data-plane "Blob Data Contributor" role.
resource "azurerm_role_assignment" "backend_blob" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = local.backend_principal_id
}

# The AI Search service only needs READ on the policies container so it can
# index handbooks — never the employee-documents (PII) container.
resource "azurerm_role_assignment" "search_policies_read" {
  scope                = azurerm_storage_container.policies.resource_manager_id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

# --- Azure OpenAI ---------------------------------------------------------
resource "azurerm_role_assignment" "backend_openai" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = local.backend_principal_id
}

# --- Azure AI Search ------------------------------------------------------
# Backend queries the index (data reader) and manages it during ingestion
# (index data contributor).
resource "azurerm_role_assignment" "backend_search_read" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = local.backend_principal_id
}

resource "azurerm_role_assignment" "backend_search_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = local.backend_principal_id
}

# Search service reads embeddings from OpenAI for integrated vectorization.
resource "azurerm_role_assignment" "search_openai" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}
