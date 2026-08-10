# Azure Blob Storage.
#
# One Hot-tier account holds onboarding documents and policy files, split into
# two strictly-segregated containers so the AI/RAG pipeline can never index
# employee PII:
#   - company-policies   : handbooks/policies (RAG has read access)
#   - employee-documents : sensitive uploads such as IDs (RAG has NO access)
#
# Blob versioning + soft delete provide data resilience against accidental
# overwrite or deletion, and a lifecycle rule tiers cold blobs down to save cost.

resource "azurerm_storage_account" "main" {
  name                     = "st${local.compact_prefix}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  # Secretless posture: disable shared-key access where possible and require
  # HTTPS + a modern TLS floor. SAS tokens are minted server-side using a
  # user-delegation key derived from the managed identity, not the account key.
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 7 # soft delete: 7-day recycle bin for blobs
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "policies" {
  name                  = "company-policies"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "documents" {
  name                  = "employee-documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle management: move rarely-accessed blobs to cool/archive over time.
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "tier-down-cold-blobs"
    enabled = true

    filters {
      blob_types = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 90
        tier_to_archive_after_days_since_modification_greater_than = 365
      }
      snapshot {
        delete_after_days_since_creation_greater_than = 90
      }
      version {
        delete_after_days_since_creation = 180
      }
    }
  }
}
