terraform {
  required_version = "= 1.17.1"
}

variable "name" {
  description = "Name of this local learning instance."
  type        = string
}

variable "labels" {
  description = "Example metadata stored only in the local Terraform state."
  type        = map(string)
  default     = {}
}

# terraform_data is built into Terraform. It stores these values in state
# without creating cloud resources, contacting Kubernetes, or running commands.
resource "terraform_data" "lab" {
  input = {
    name   = var.name
    labels = var.labels
  }
}

output "lab" {
  description = "The metadata recorded for this local learning instance."
  value       = terraform_data.lab.output
}
