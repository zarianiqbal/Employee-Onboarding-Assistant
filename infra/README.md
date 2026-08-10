# Infrastructure (Terraform)

Declarative Azure infrastructure for the Employee Onboarding Assistant. All
resources are provisioned as code — no manual portal "ClickOps".

## Resources provisioned

| File                 | Resources                                                  |
| -------------------- | ---------------------------------------------------------- |
| `main.tf`            | Resource group, naming, random suffix                      |
| `storage.tf`         | Storage account, 2 segregated containers, versioning, soft delete, lifecycle |
| `sql.tf`             | SQL server (Entra-only auth) + database                    |
| `app_service.tf`     | Linux App Service + plan, system-assigned managed identity |
| `ai.tf`              | Azure OpenAI (chat + embeddings) + Azure AI Search         |
| `identity.tf`        | RBAC role assignments (secretless access)                  |
| `observability.tf`   | Log Analytics + Application Insights                        |

## Secretless by design

- No SQL passwords: the server is **Entra-ID-only**; the App Service managed
  identity is granted DB access.
- No storage keys: SAS tokens are minted from a **user-delegation key** derived
  from the managed identity; static key auth is disabled where possible.
- No OpenAI/Search keys: `local_auth` is disabled; access is via **RBAC**.

## Usage

```bash
# One-time: bootstrap the remote-state storage account, then:
terraform init \
  -backend-config="resource_group_name=rg-onboarding-tfstate" \
  -backend-config="storage_account_name=stonboardingtfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=onboarding.tfstate"

terraform plan  -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

See `example.tfvars` for the variables to supply.

## CI/CD

`terraform fmt -check` and `terraform validate` run on every PR
(`.github/workflows/infra.yml`). Applies are gated behind PR review and run via
OIDC federation (no long-lived cloud credentials in GitHub secrets).
