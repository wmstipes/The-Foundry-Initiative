include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/forge-lab"
}

inputs = {
  name = "lab-b"
  labels = {
    project = "forge"
    lesson  = "reuse-with-different-inputs"
  }
}
