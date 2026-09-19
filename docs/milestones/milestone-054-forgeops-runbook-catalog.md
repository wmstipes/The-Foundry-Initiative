# Milestone 054 — ForgeOps validated runbook knowledge catalog

**Status:** Implemented and accepted locally; publication in progress

**Started:** 2026-09-19

**Implementation branch:** `codex/milestone-054-forgeops-runbook-catalog`

**Baseline:** clean `main` at `c8ad7b6e8a7e740521446cb23a039b71f09f82d1`

## Goal

Establish a strict, machine-readable catalog of repository-owned runbook
sections and the bounded ForgeOps signals they discuss. The catalog provides
grounding data for a later mapping milestone; validation alone does not select
a runbook or claim that any procedure applies to an incident.

## Interface

~~~powershell
forgeops runbook catalog validate `
  --input .\docs\reference\forgeops-runbook-catalog.json
~~~

The command reads exactly one explicit local file, validates it, reports only
bounded counts, and returns `0` for a valid catalog or `2` for invalid input.

## Contract

`forgeops.runbook-catalog/v1alpha1` contains:

- sorted, unique stable entry identifiers;
- human-readable titles;
- repository-relative Markdown paths restricted to `docs/runbooks`;
- exact section headings;
- sorted exact or prefix check-identifier selectors;
- canonical non-empty delta-kind and after-status sets; and
- one fixed limitation statement.

The canonical catalog contains seven entries and fourteen selectors covering
node readiness, workload rollout, Pod state, Service routing, the Metrics API,
Restaurant API endpoints, and recovery verification. Repository tests prove
that every referenced file and heading exists.

## Trust and authority boundary

- Catalog validation does not load evidence or comparison artifacts.
- It does not determine applicability, rank procedures, infer causes, assign
  severity, diagnose an incident, recommend an action, or execute a runbook.
- It invokes no collector, kubectl runner, HTTP runner, network, discovery,
  persistence, retrieval service, model, or mutation path.
- A catalog entry is maintained repository knowledge, not proof that its
  procedure is correct for a particular operational event.

## Acceptance

- Strict bounded parsing rejects oversized input, invalid UTF-8, malformed
  JSON, duplicate keys, unknown or unordered fields, invalid selectors,
  unsafe paths, unsupported values, duplicates, and noncanonical ordering.
- The canonical catalog validates with seven entries and fourteen signals.
- Every canonical path and section heading resolves in the repository.
- Invalid-input messages omit operator-supplied paths.
- The complete repository test suite, isolated installation, source execution,
  compilation, manifest validation, and whitespace validation pass offline.

## Explicit exclusions

- No runbook mapping command or serialized mapping result.
- No incident brief, causal reasoning, diagnosis, recommendation, retrieval,
  language model, remediation, or cluster mutation.
- No package/image publication, release tag, deployment, live acceptance,
  cluster access, endpoint access, persistent-state change, or Wiki mutation.

## Gates

1. Scope and design — pre-approved and complete.
2. Local implementation and offline acceptance — pre-approved and complete.
3. Publication and pull request — pre-approved; in progress.
4. Package/image release — closed as not applicable.
5. Deployment — closed as not applicable.
6. Live acceptance — closed as not applicable.
7. Ready for review — pre-approved; pending publication and CI.
8. Merge — pre-approved; pending publication and CI.
9. Documentation-only closeout — pre-approved; pending implementation merge.
10. Branch cleanup — pre-approved; pending closeout merge.
