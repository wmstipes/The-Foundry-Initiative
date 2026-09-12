# Milestone 034 — Forge YAML Workbench deeper deterministic checks

Started: 2026-09-12

Status: Implementation, local verification, pull-request CI, and non-publishing multi-architecture build complete in draft PR #10. Browser acceptance, release publication, deployment, and merge remain separate checkpoints.

## Goal

Make each Workbench operational finding more actionable and add bounded cross-resource checks that can be evaluated deterministically in the browser.

## Bounded scope

- Give every operational finding a precise YAML path.
- Separate the explanation of the risk from a suggested correction.
- Detect missing or mismatched workload selectors.
- Detect duplicate resource identities in multi-document input.
- Compare Service selectors with workload Pod labels included in the same file.
- Validate named Service target ports against selected workload container-port names.
- Detect host PID and IPC namespace sharing in addition to existing host-network and HostPath checks.
- Check whether containers explicitly disable privilege escalation, use a read-only root filesystem, drop Linux capabilities, and require non-root execution.
- Preserve existing parser diagnostics, summaries, formatting, object tree, file handling, and keyboard behavior.
- Report parsed-document and finding counts without implying API-server validity.

## Guardrails

- YAML remains in browser memory and is not sent to a backend.
- The Workbench receives no Kubernetes credentials or API access.
- No server-side persistence is introduced.
- Cross-document checks use only resources included in the current editor input.
- A standalone Service does not produce a false missing-workload warning when no comparable workload is included.
- `matchExpressions` selectors are accepted but are not fully evaluated in this milestone.
- Findings remain bounded operational guidance, not Kubernetes schema or admission guarantees.
- No application version bump, image publication, or live cluster change is included without a later explicit checkpoint.

## Acceptance gates

- [x] Analyzer tests cover paths, corrections, selector mismatch, selector expressions, duplicate identities, Service selection, named target ports, host namespaces, and container hardening.
- [x] DOM coverage confirms paths and suggested corrections are rendered in Validation.
- [x] Locked clean installation, 20-test suite, production build, dependency audit, repository manifest validation, and whitespace checks pass locally.
- [x] Pull-request CI and non-publishing multi-architecture image build pass.
- [ ] Browser acceptance passes against representative valid and intentionally flawed manifests.
- [ ] Any versioned publication is separately approved and verified.
- [ ] Any live Deployment update is separately dry-run, diff-reviewed, approved, and verified.
- [ ] Final review and merge are separately approved.

## Deferred

- Kubernetes OpenAPI schema validation remains Milestone 035.
- Full set-based evaluation of `matchExpressions` is deferred unless a later bounded requirement justifies it.
- Cluster lookups, admission requests, policy-engine integration, and automatic YAML mutation remain out of scope.
