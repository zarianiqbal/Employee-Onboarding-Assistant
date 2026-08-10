# Azure SQL Database.
#
# The server uses Entra ID (Azure AD) authentication only — SQL logins with
# static passwords are disabled. The App Service managed identity is granted
# access at the database level (see identity.tf / post-deploy grants), so the
# backend never needs a connection-string password.

resource "azurerm_mssql_server" "main" {
  name                         = "sql-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  minimum_tls_version          = "1.2"
  public_network_access_enabled = true

  # Entra-only auth: no SQL admin username/password.
  azuread_administrator {
    login_username              = var.sql_admin_login
    object_id                   = var.sql_admin_object_id
    azuread_authentication_only = true
  }

  tags = var.tags
}

resource "azurerm_mssql_database" "main" {
  name           = "sqldb-${local.name_prefix}"
  server_id      = azurerm_mssql_server.main.id
  sku_name       = var.environment == "prod" ? "S1" : "Basic"
  max_size_gb    = var.environment == "prod" ? 50 : 2
  zone_redundant = false
  collation      = "SQL_Latin1_General_CP1_CI_AS"

  tags = var.tags
}

# Allow other Azure services (e.g. the App Service) to reach the SQL server.
resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
