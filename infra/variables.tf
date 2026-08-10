# Input variables for the onboarding infrastructure.

variable "project" {
  description = "Short project slug used to name resources."
  type        = string
  default     = "onboarding"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "eastus"
}

variable "sql_admin_login" {
  description = "Entra ID admin login (UPN or group name) for the SQL server."
  type        = string
}

variable "sql_admin_object_id" {
  description = "Entra ID object id of the SQL admin principal."
  type        = string
}

variable "openai_deployments" {
  description = "Azure OpenAI model deployments to create."
  type = map(object({
    model_name    = string
    model_version = string
    capacity      = number
  }))
  default = {
    chat = {
      model_name    = "gpt-4o"
      model_version = "2024-08-06"
      capacity      = 20
    }
    embeddings = {
      model_name    = "text-embedding-3-large"
      model_version = "1"
      capacity      = 20
    }
  }
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default = {
    application = "employee-onboarding-assistant"
    managed_by  = "terraform"
  }
}
