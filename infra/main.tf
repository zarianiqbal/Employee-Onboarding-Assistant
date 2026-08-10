# Core resource group + naming.
#
# A single random suffix keeps globally-unique names (storage, OpenAI, search)
# stable within a state while avoiding collisions across environments.

locals {
  name_prefix = "${var.project}-${var.environment}"
  # Storage / OpenAI / Search names must be globally unique and alphanumeric.
  compact_prefix = replace("${var.project}${var.environment}", "-", "")
}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = var.tags
}
