# Example variable values. Copy to a real *.tfvars file (git-ignored) and fill
# in your environment's values, or pass via -var on the command line / CI.

project     = "onboarding"
environment = "dev"
location    = "eastus"

# Entra ID principal that administers the SQL server (a group is recommended).
sql_admin_login     = "onboarding-sql-admins"
sql_admin_object_id = "00000000-0000-0000-0000-000000000000"
