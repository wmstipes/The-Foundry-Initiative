# Forge Terraform and Terragrunt learning pilot

**Prepared:** 2026-10-29

**Scope:** Local learning exercise; no cluster or cloud resources.

**Versions:** Terraform `1.17.1`, Terragrunt `1.2.1`.

This pilot introduces infrastructure as code to Forge in two steps: understand
one Terraform module, then reuse it through Terragrunt with two independent
configurations. It gives the planned infrastructure-as-code work in
[Roadmap Phase 7](../../ROADMAP.md#phase-7--portfolio-and-hybrid-cloud-expansion)
a small, runnable starting point. The next platform deployment objective remains
[central logging coverage](../../docs/runbooks/identity-logging-plan.md).

## What the tools do

| Tool | Responsibility |
| --- | --- |
| Terraform | Evaluates resource definitions, plans changes, applies them and records state. |
| Terragrunt | Runs Terraform, passes inputs and shares configuration across independent units. |
| Helm | Packages related Kubernetes resources as charts; existing Forge releases retain their current ownership. |
| Kubernetes | Runs and reconciles the resources deployed to the cluster. |

Terragrunt also supports OpenTofu. This example explicitly chooses Terraform
to make the engine visible while learning. Terragrunt is a workstation or CI
command-line tool; it does not need a persistent service on the Raspberry Pis.

The module uses only the built-in `terraform_data` resource. Its name and labels
are written to local state. There are no external providers, remote modules,
provisioners, hooks, Kubernetes credentials or cloud credentials. Applying this
exercise does not create a namespace or any other infrastructure. A successful
run demonstrates the workflow, not Forge cluster health or cloud provisioning.

## Files and state

| Path | Purpose |
| --- | --- |
| `modules/forge-lab/main.tf` | One reusable module with inputs, a resource and an output. |
| `direct/main.tf` | Runs that module using Terraform alone. |
| `live/root.hcl` | Shared engine/version constraints and local-backend generation. |
| `live/lab-a/terragrunt.hcl` | First Terragrunt unit with its own inputs. |
| `live/lab-b/terragrunt.hcl` | Second unit reusing the same module. |

Each of the three examples has its own `.state/terraform.tfstate` beside its
source configuration. Terragrunt generates an absolute backend path, so state
survives replacement of `.terragrunt-cache`. These are independent learning
instances, not copies of the same managed infrastructure.

State, saved plans, generated backends and caches are ignored by Git. Provider
lock files remain trackable; none is required for this built-in-only module.
Use this local state on one workstation. Managing shared infrastructure from
multiple machines or CI would first require a deliberate backend, locking,
access-control and backup decision. Do not copy this state pattern into a
shared deployment without that design.

## Install the two tools

Install exactly the versions above using the official
[Terraform downloads](https://releases.hashicorp.com/terraform/1.17.1/) and
[Terragrunt installation instructions](https://docs.terragrunt.com/getting-started/install/).
Choose Windows amd64 for the Windows laptop, or Linux arm64 for the Spark.
Verify the selected release checksum and its available signature/attestation
before placing the binaries on your `PATH`. This repository does not install
tools globally or change your shell profile.

```text
terraform version
terragrunt --version
```

The source enforces both exact versions. Review and validate version updates
together. An explicit `--tf-path` or `TG_TF_PATH` can override the engine selected
in `root.hcl`; use the intended Terraform binary for this exercise.

## Step 1: Terraform first

Start in `experiments/terragrunt-lab` in the repository. These commands work in
PowerShell and Bash:

```text
terraform -chdir=direct init
terraform -chdir=direct validate
terraform -chdir=direct plan -out=lab.tfplan
terraform -chdir=direct show lab.tfplan
```

Read the plan. Expect one `module.forge_lab.terraform_data.lab` resource with
the name `direct`. Then apply that saved plan and inspect the output:

```text
terraform -chdir=direct apply lab.tfplan
terraform -chdir=direct output
terraform -chdir=direct plan -detailed-exitcode
```

Applying a saved plan executes it without another confirmation prompt. In this
exercise it records only local metadata. A repeated plan should report no
changes: exit `0` means no changes, `2` means changes are proposed, and `1`
means an error. The direct example shows what Terraform does before adding
Terragrunt.

## Step 2: Reuse the module through Terragrunt

In PowerShell, starting again from the lab directory:

```powershell
Set-Location live/lab-a
$forgePlan = Join-Path (Get-Location).Path "lab.tfplan"
terragrunt run -- init
terragrunt run -- validate
terragrunt run -- plan -out="$forgePlan"
terragrunt run -- show "$forgePlan"
```

After reviewing the one-resource plan:

```powershell
terragrunt run -- apply "$forgePlan"
terragrunt run -- output
terragrunt run -- plan -detailed-exitcode
```

In Bash, the equivalent setup is:

```bash
cd live/lab-a
forge_plan="$PWD/lab.tfplan"
terragrunt run -- init
terragrunt run -- validate
terragrunt run -- plan -out="$forge_plan"
terragrunt run -- show "$forge_plan"
# Review the plan before the next command.
terragrunt run -- apply "$forge_plan"
terragrunt run -- output
terragrunt run -- plan -detailed-exitcode
```

Expect the output name `lab-a`. Repeat from `live/lab-b`, assigning a new
absolute plan path in that directory; its output should be `lab-b`. An absolute
saved-plan path keeps it outside Terragrunt's generated working directory.
The inputs differ, while the module and backend rules are shared.

From `live`, inspect both units together:

```text
terragrunt run --all -- plan -detailed-exitcode
```

After both individual applies, this should report no changes. Use the individual
saved-plan workflow for applies. Terragrunt's all-unit apply/destroy mode adds
automatic approval to the underlying engine; it is not used in this pilot.
These two units are independent, so this exercise does not demonstrate
dependency ordering.

## Finish line and cleanup

The lesson is complete when you can explain the module, inputs, output and state;
show different outputs for `lab-a` and `lab-b`; and obtain a no-change plan for
both. Change one unit's `name`, inspect its proposed update, and confirm the
other unit still has no changes. Restore the input before finishing if you do
not want to apply that change.

To remove the local learning records, use `terraform -chdir=direct destroy`
from the lab directory and `terragrunt run -- destroy` from each unit directory.
Review each prompt. These commands affect only this example's built-in state
records. Keep these cleanup commands scoped to these directories.

## Validation record — October 29, 2026

In an isolated Linux amd64 checkout, the pinned binaries were downloaded from
their official release locations and matched their published SHA-256 checksums.
Terraform formatting and Terragrunt HCL formatting passed. All three examples
passed initialization, validation, saved-plan application, output/state identity
checks and repeated no-change plans. Both Terragrunt caches were removed and
recreated; each retained its state and again produced a no-change plan. A
changed `lab-a` input produced plan exit `2`, while `lab-b` remained exit `0`.
The combined two-unit plan returned `0`.
Scoped cleanup of all three local learning records also passed.

This is local binary execution evidence. Windows and Linux arm64 acceptance,
user walkthrough, hosted Terragrunt CI and live infrastructure integration
remain separate follow-ups. Existing application test counts are unchanged.

## First real integration, after the lesson

The proposed next exercise is a new `forge-iac-lab` namespace and one benign
ConfigMap, with explicit resource ownership and a reviewed plan. Select and pin
the Kubernetes provider, establish scoped credentials, and decide state storage
before implementing it. Existing identity, gateway, Helm releases and persistent
volumes are outside that first exercise. The learning pilot creates none of
those resources and does not replace the agreed logging work.

## Primary references

- [Terragrunt quick start](https://docs.terragrunt.com/getting-started/quick-start/)
- [Shared root configuration](https://docs.terragrunt.com/migrate/migrating-from-root-terragrunt-hcl/)
- [Engine and version attributes](https://docs.terragrunt.com/reference/hcl/attributes/)
- [Terragrunt run command](https://docs.terragrunt.com/reference/cli/commands/run/)
- [Terragrunt cache](https://docs.terragrunt.com/features/units/terragrunt-cache/)
- [Terraform data resource](https://developer.hashicorp.com/terraform/language/resources/terraform-data)
- [Terraform local backend](https://developer.hashicorp.com/terraform/language/backend/local)
- [Helm charts](https://helm.sh/docs/topics/charts/)
