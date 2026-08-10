# Provider configuration.
#
# Authentication is secretless: in CI the azurerm provider authenticates via
# OIDC federation with GitHub Actions (ARM_USE_OIDC=true), and locally via the
# Azure CLI. No client secrets are stored in code or state.

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

provider "azuread" {}

provider "random" {}
