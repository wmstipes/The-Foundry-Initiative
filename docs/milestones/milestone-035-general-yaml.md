# Milestone 035 — General YAML inspection mode

Started: 2026-09-13

Status: Source implementation and local automated validation complete on `codex/milestone-035-general-yaml`. Publication, deployment, live acceptance, and merge remain separate approval checkpoints.

## Goal

Add an explicit General YAML inspection mode alongside the existing Kubernetes mode without weakening the Workbench's browser-local processing boundary or implying Kubernetes schema validation.

## Bounded scope

- Keep Kubernetes as the default inspection mode.
- Allow an explicit switch between Kubernetes and General YAML inspection without modifying editor contents.
- Share YAML parsing, formatting, parser diagnostics, file open/download handling, keyboard shortcuts, and tree navigation across both modes.
- Accept mapping, sequence, and scalar document roots in General YAML mode.
- Summarize General YAML documents by root type and top-level shape.
- Suppress Kubernetes resource summaries, operational checks, remediation guidance, and OWASP references in General YAML mode.
- Preserve all Milestone 034 Kubernetes behavior when Kubernetes mode is selected.

## Guardrails

- YAML remains in browser memory and is not sent to a backend.
- The Workbench receives no Kubernetes credentials or API access.
- Switching modes does not transform, clear, upload, or persist the YAML.
- General YAML mode performs syntax and structure inspection only.
- Kubernetes remains the startup default.
- No Kubernetes OpenAPI schema bundle or validation is introduced.
- No additional OWASP Kubernetes Top 10 rules are introduced.
- No image publication, manifest update, cluster deployment, or merge occurs without its separate approval checkpoint.

## Acceptance gates

- [x] Analyzer coverage proves Kubernetes remains the default and continues rejecting non-mapping roots.
- [x] Analyzer coverage proves General YAML accepts mapping, sequence, and scalar roots.
- [x] Analyzer coverage proves Kubernetes-only findings are absent in General YAML mode.
- [x] DOM coverage proves mode switching preserves editor content and updates the report boundary.
- [x] DOM coverage proves scalar summaries render and Kubernetes findings remain hidden in General YAML mode.
- [x] Existing parser, formatter, file handling, location navigation, and remediation tests remain green.
- [x] Production build and whitespace validation pass locally.
- [x] Clean locked installation, dependency audit, and repository validation pass.
- [ ] Pull-request CI and non-publishing multi-architecture image build pass.
- [ ] Live browser acceptance passes for both modes after an approved deployment.
- [ ] Versioned `0.3.0` publication is separately approved and its AMD64/ARM64 OCI index digest is recorded.
- [ ] Deployment is separately dry-run, diff-reviewed, approved, rolled out, and runtime-verified at the pinned digest.
- [ ] Final review and merge are separately approved.

## Deferred

- Browser-local Kubernetes schema validation remains Milestone 036.
- Broader OWASP Kubernetes Top 10:2025 coverage remains Milestone 037.
- Formatting diff, report export, finding filters, tree search, drag-and-drop, display preferences, and bounded large-file behavior remain later increments.
- Cluster lookups, admission requests, policy-engine integration, automatic YAML mutation, and server-side persistence remain out of scope.
