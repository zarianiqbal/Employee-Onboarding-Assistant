# Outputs consumed by CI/CD (deploy target) and local development.

output "resource_group_name" {
  description = "Name of the resource group."
  value       = azurerm_resource_group.main.name
}

output "backend_app_name" {
  description = "App Service name (deploy target for GitHub Actions)."
  value       = azurerm_linux_web_app.backend.name
}

output "backend_default_hostname" {
  description = "Public hostname of the backend App Service."
  value       = azurerm_linux_web_app.backend.default_hostname
}

output "sql_server_fqdn" {
  description = "Fully-qualified domain name of the SQL server."
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  description = "Onboarding database name."
  value       = azurerm_mssql_database.main.name
}

output "storage_account_name" {
  description = "Blob storage account name."
  value       = azurerm_storage_account.main.name
}

output "storage_blob_endpoint" {
  description = "Primary blob endpoint URL."
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint."
  value       = azurerm_cognitive_account.openai.endpoint
}

output "search_endpoint" {
  description = "Azure AI Search endpoint."
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}
