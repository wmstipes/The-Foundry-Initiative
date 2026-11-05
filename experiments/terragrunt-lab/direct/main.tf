terraform {
  required_version = "= 1.17.1"

  backend "local" {
    path = ".state/terraform.tfstate"
  }
}

module "forge_lab" {
  source = "../modules/forge-lab"
  name   = "direct"

  labels = {
    project = "forge"
    lesson  = "terraform-first"
  }
}

output "lab" {
  description = "The same module output later exposed through Terragrunt."
  value       = module.forge_lab.lab
}
