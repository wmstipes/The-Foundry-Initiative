# Both units use the same engine and version pins.
terraform_binary              = "terraform"
terraform_version_constraint  = "= 1.17.1"
terragrunt_version_constraint = "= 1.2.1"

locals {
  # Each unit keeps its state beside its source configuration, outside the cache.
  state_path = abspath("${get_original_terragrunt_dir()}/.state/terraform.tfstate")
}

generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    terraform {
      backend "local" {
        path = ${jsonencode(local.state_path)}
      }
    }
  EOF
}
