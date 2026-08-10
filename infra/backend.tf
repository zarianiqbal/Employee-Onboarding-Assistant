# Remote state backend.
#
# Terraform state is stored and locked in Azure Blob Storage so the whole team
# can collaborate safely (blob leases prevent two pipelines mutating infra at
# once). The backing storage account/container are bootstrapped once, out of
# band, before the first `terraform init`.
#
# Values are supplied at init time to avoid hardcoding subscription-specific
# names here, e.g.:
#
#   terraform init \
#     -backend-config="resource_group_name=rg-onboarding-tfstate" \
#     -backend-config="storage_account_name=stonboardingtfstate" \
#     -backend-config="container_name=tfstate" \
#     -backend-config="key=onboarding.tfstate"

terraform {
  backend "azurerm" {
    use_oidc = true
  }
}
