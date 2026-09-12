# Milestone 034 — Forge YAML Workbench deeper deterministic checks

Started: 2026-09-12

Status: Implementation, local verification, pull-request CI, non-publishing multi-architecture build, and browser acceptance complete in draft PR #10. Release publication, deployment, final review, and merge remain separate checkpoints.

## Goal

Make each Workbench operational finding more actionable and add bounded cross-resource checks that can be evaluated deterministically in the browser.

## Bounded scope

- Give every operational finding a precise YAML path.
- Make each YAML path navigate to the nearest existing editor location, including a useful parent location for a missing field.
- Separate the explanation of the risk from a suggested correction.
- Provide expandable, copyable YAML examples and workload-specific cautions for OWASP K01 hardening findings.
- Identify OWASP K01:2025 findings with a direct source link.
- Detect missing or mismatched workload selectors.
- Detect duplicate resource identities in multi-document input.
- Compare Service selectors with workload Pod labels included in the same file.
- Validate named Service target ports against selected workload container-port names.
- Detect host PID and IPC namespace sharing in addition to existing host-network and HostPath checks.
- Check whether containers explicitly disable privilege escalation, use a read-only root filesystem, drop Linux capabilities, require non-root execution, and use a RuntimeDefault or Localhost seccomp profile.
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
- OWASP references identify relevant guidance and do not imply full OWASP coverage or compliance certification.
- Suggested YAML is copied for operator review; the Workbench does not automatically mutate the manifest.
- No application version bump, image publication, or live cluster change is included without a later explicit checkpoint.

## Acceptance gates

- [x] Analyzer tests cover paths, corrections, selector mismatch, selector expressions, duplicate identities, Service selection, named target ports, host namespaces, container hardening, seccomp, and OWASP K01 remediation metadata.
- [x] DOM coverage confirms paths, expandable guidance, cautions, OWASP references, and copyable YAML are rendered in Validation.
- [x] Locked clean installation, 23-test suite, production build, dependency audit, repository manifest validation, and whitespace checks pass locally.
- [x] Pull-request CI and non-publishing multi-architecture image build pass.
- [x] Browser acceptance passes for clickable paths, expandable remediation guidance, copyable YAML, cautions, and OWASP references.
- [ ] Any versioned publication is separately approved and verified.
- [ ] Any live Deployment update is separately dry-run, diff-reviewed, approved, and verified.
- [ ] Final review and merge are separately approved.

## Deferred

- Kubernetes OpenAPI schema validation remains Milestone 035.
- Broader OWASP Kubernetes Top 10:2025 coverage remains a separate milestone after schema validation.
- Full set-based evaluation of `matchExpressions` is deferred unless a later bounded requirement justifies it.
- Cluster lookups, admission requests, policy-engine integration, and automatic YAML mutation remain out of scope.
