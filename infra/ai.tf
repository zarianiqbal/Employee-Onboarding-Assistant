# Azure OpenAI + Azure AI Search (the RAG tier).
#
# OpenAI hosts the chat + embedding model deployments; AI Search holds the
# vector index built from policy PDFs. Both use Entra ID auth (local/key auth
# disabled) so the backend's managed identity is the only path in.

resource "azurerm_cognitive_account" "openai" {
  name                  = "oai-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name   = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "oai-${local.compact_prefix}${random_string.suffix.result}"

  # Secretless: force Entra ID auth, disable static API keys.
  local_auth_enabled = false

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "models" {
  for_each = var.openai_deployments

  name                 = each.key
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = each.value.model_name
    version = each.value.model_version
  }

  scale {
    type     = "Standard"
    capacity = each.value.capacity
  }
}

resource "azurerm_search_service" "main" {
  name                = "srch-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "standard" : "basic"
  replica_count       = 1
  partition_count     = 1

  # Secretless: RBAC-based data plane auth only, no admin/query keys.
  local_authentication_enabled = false
  authentication_failure_mode  = null

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
