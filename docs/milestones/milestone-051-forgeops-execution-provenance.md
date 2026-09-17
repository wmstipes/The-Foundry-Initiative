# Milestone 051 — ForgeOps trustworthy execution provenance

**Status:** Implementation merged through PR #41 at `e5e2a0898480e7722295e8df5e35eb25d4829848`; documentation-only closeout in progress

**Started:** 2026-09-17

**Implementation branch:** `codex/milestone-051-forgeops-execution-provenance`

**Baseline:** `main` at `59cad31d28eee0d41e345a105b306f5165444cd5`

## Goal

Make the executing ForgeOps version, source, and Python interpreter explicit;
replace the global editable-install recommendation with supported isolated
operator and source-development modes; and consolidate current ForgeOps concepts
into one operator and learning guide.

This milestone addresses execution provenance only. It does not claim evidence
authenticity, artifact integrity, or chain of custody.

## Why this is the next bounded increment

During the read-only learning checkpoint, Python 3.14 resolved ForgeOps through
an older editable installation under `AppData\Local\Temp\forgeops-m046-live-...`.
Consequently, `python -m forgeops` exposed the Milestone 046 command surface even
though the repository had advanced through Milestone 050.

The repository source, package metadata, and CI were internally consistent. The
problem was operator execution identity: Python correctly followed stale
editable-install metadata, while the command provided no direct way to show its
loaded source. Adding further consumers or reasoning before closing that gap
would weaken operator trust.

## Delivered interface

~~~powershell
forgeops provenance
~~~

The report contains:

- distribution name and version;
- loaded ForgeOps module version and path;
- Python executable;
- execution mode;
- recorded install or declared source location; and
- explicit findings and status.

Provenance exit `0` means identity is consistent, `1` means the visible identity
requires review, and `2` means it is inconsistent. These semantics are separate
from snapshot, evidence-validation, and comparison exit codes.

## Supported execution modes

- **Operator:** repository-local `.venv` with a normal `pip install .`.
- **Development:** `scripts/run-forgeops-dev.py`, which resolves its repository
  root, selects that exact `src` tree before importing ForgeOps, declares the
  source root for validation, and invokes the normal CLI inside one process.

A global editable install is no longer the recommended operator path. A
deliberate editable development install must be isolated, point to a stable
checkout, and be inspected with the provenance command.

## Detection boundary

The provenance component:

- uses Python runtime and installed-distribution metadata only;
- checks declared source mode against `pyproject.toml` and the loaded path;
- reports a version mismatch as an error;
- reports a missing editable source or a module outside that source as an error;
- reports an editable source under the operating-system temporary directory as
  a warning; and
- reports missing distribution metadata as a warning unless the supported
  source launcher declares and validates source mode.

The report intentionally includes local paths because that is required to
identify stale execution. Operators must review it before sharing.

## Explicit exclusions

- No kubeconfig, kubectl, HTTP, DNS, or network access.
- No Kubernetes or application collection.
- No evidence loading, comparison, replay, or persistence.
- No artifact hash, signing, attestation, authorship, authenticity, or chain-of-
  custody claim.
- No scenario runner, runbook mapping, diagnosis, recommendation, language
  model, AI reasoning, remediation, or mutation.
- No registry package, image, release tag, manifest, deployment, cluster access,
  endpoint access, persistent-state change, or Wiki mutation.

## Documentation consolidation

`docs/guides/forgeops-operator-learning-guide.md` now owns the consolidated
current explanation of:

- supported execution modes and stale-install recovery;
- execution provenance;
- architecture and component responsibilities;
- command and evidence flow;
- four separate exit-code domains; and
- trust and authority boundaries.

The existing runbook remains procedural. Milestones 044-050 remain unchanged as
chronological evidence and are linked rather than rewritten.

## Testing strategy

Offline tests cover:

- explicit CLI parsing and rendering;
- a matching normal installation;
- distribution/module version mismatch;
- a temporary editable installation;
- declared source mode with matching project, module, and path;
- deterministic report fields and findings; and
- proof that provenance constructs no collection or network runner.

Isolated-install acceptance must additionally prove the normal installed entry
point reports `OK`, while source-mode acceptance proves the current checkout is
selected explicitly. No acceptance step requires SignalForge access.

Local acceptance passes all 79 focused ForgeOps tests and all 137 repository
tests. An isolated non-editable `foundry-check==0.7.0` installation reports
matching distribution and module versions, `local-install` mode, the isolated
Python executable, and status `OK`. The source launcher reports matching source
project and module versions, the repository module path, `source` mode, and
status `OK`. Installed command entry checks, Python compilation, Kubernetes
manifest validation, and whitespace validation also pass.

## Release and deployment impact

- Repository-local package metadata advances from `0.6.0` to `0.7.0`.
- No package is published to a registry.
- No image, release tag, manifest, workload, ServiceAccount, RBAC, Service,
  configuration, or persistent state changes.
- No deployment, rollout, restart, live acceptance, cluster access, application
  endpoint access, or Wiki change.

Gates 4-6 were explicitly approved and closed as not applicable. No release,
deployment, or live acceptance action occurred.

## Publication evidence

- Draft pull request: #41.
- Published branch: `codex/milestone-051-forgeops-execution-provenance`.
- Accepted local implementation commit: `7443a278fc638458a036ed5251e7d1aa7e29903c`.
- Published implementation commit: `8dc35c862e4c6a30e59af2c33d4512757c82772c`.
- Exact matching local and published tree: `621d1cfbc0faf8257a4711f6b6747172694a7ed7`.
- Final published head: `4e5e7334448fb734fdc7e1f869d7215c8855c4cc`.
- Final accepted and published tree: `652d01fdb7933e037b0097170610ea8480164588`.
- Final-head ForgeOps CI run `35265922723` completed successfully.
- PR #41 was marked ready under Gate 7 and merged under Gate 8 at
  `e5e2a0898480e7722295e8df5e35eb25d4829848`.
- The merge commit resolves to exact accepted tree
  `652d01fdb7933e037b0097170610ea8480164588`.
- The repository connector was used because this runtime's HTTPS Git client has
  no credential helper.

## Relationship to later work

Execution provenance answers which code is running. A later evidence-integrity
milestone may separately define hashes, metadata, or stronger authenticity
mechanisms. Scenario replay, grounded runbook mapping, and bounded incident
reasoning remain separate capabilities with separate approval boundaries.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete; deterministic offline acceptance passes.
3. Publication and draft PR — approved and complete through draft PR #41; the published implementation tree exactly matches the accepted local tree.
4. Package or image release — approved disposition and closed as not applicable; no distribution, image, or release tag was published.
5. Deployment — approved disposition and closed as not applicable; no deployable artifact, manifest, workload, configuration, or persistent state changed.
6. Live acceptance — approved disposition and closed as not applicable; acceptance remained entirely offline with no cluster or endpoint access.
7. Pull-request readiness — approved and complete after successful final-head ForgeOps CI run `35265922723`.
8. Merge — approved and complete; PR #41 merged at `e5e2a0898480e7722295e8df5e35eb25d4829848`, preserving accepted tree `652d01fdb7933e037b0097170610ea8480164588`.
9. Closeout — approved and in progress through documentation-only branch `codex/milestone-051-closeout`.
10. Branch cleanup — approved and pending closeout merge verification.
