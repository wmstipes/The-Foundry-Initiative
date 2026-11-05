include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/forge-lab"
}

inputs = {
  name = "lab-a"
  labels = {
    project = "forge"
    lesson  = "shared-configuration"
  }
}
