# Milestone 048 — ForgeOps deterministic offline evidence comparison

**Status:** Local implementation and offline validation complete; publication and later gates remain separately gated

**Started:** 2026-09-16

**Branch:** `codex/milestone-048-forgeops-evidence-comparison`

**Baseline:** `main` at `2ebaa902f56f6b143009c4e630ba95f4a03759d8`

## Goal

Compare two contract-validated `forgeops.snapshot/v1alpha1` artifacts deterministically and report exactly what changed without collecting new evidence or inferring causes.

The milestone extends the one-way authority path:

```text
bounded collection
→ selected-field normalization
→ deterministic evaluation
→ redacted evidence artifact
→ strict offline validation
→ deterministic offline comparison
→ optional future reasoning
```

## Audience

- The SignalForge operator comparing two saved point-in-time snapshots.
- Developers building later scenario replay or evidence-grounded reasoning.
- Technical reviewers evaluating deterministic and least-authority operations tooling.

## Delivered interface

~~~powershell
forgeops evidence compare `
  --before .\forgeops-snapshot-before.json `
  --after .\forgeops-snapshot-after.json
~~~

Both artifacts must independently satisfy the Milestone 047 validator before comparison output is produced.

## Comparison semantics

- Read two explicitly selected regular files through the existing bounded loader.
- Enforce the existing 1 MiB per-file limit, UTF-8 JSON contract, duplicate-key rejection, exact schema, and summary validation.
- Reject an `after` collection timestamp earlier than `before`; equal timestamps remain valid.
- Match checks by unique check identifier.
- Sort results by identifier independently from artifact order.
- Report a check present only in `after` as `ADDED`.
- Report a check present only in `before` as `REMOVED`.
- Report a status transition as `STATUS_CHANGED`.
- Report a change to observation, source, expected, observed, or error category without a status transition as `EVIDENCE_CHANGED`.
- Display collection timestamps but do not classify them as changes.
- Return an immutable `EvidenceComparison` containing immutable `CheckDelta` values.

Exit codes describe comparison execution, not the health inside either artifact:

- `0`: both artifacts are valid and operationally equivalent;
- `1`: both artifacts are valid and at least one check differs; and
- `2`: an artifact or the requested chronology is invalid.

## Explicit exclusions

- No kubeconfig, kubectl, subprocess, HTTP, DNS, or network access.
- No collection, discovery, new telemetry, or expansion of the SignalForge allowlist.
- No artifact repair, rewrite, copy, retention, history, database, or storage authority.
- No duration analysis, causal inference, severity scoring, diagnosis, runbook mapping, recommendation, replay, or remediation.
- No JSON or other serialized comparison contract in this milestone.
- No language model, retrieval system, or AI reasoning.
- No package registry, image, release tag, manifest, deployment, Wiki, or cluster action.
- No mutation authority.

## Implementation

`src/forgeops/comparison.py` owns the immutable comparison model, chronology check, field-level comparison, deterministic ordering, and text renderer. It accepts only `ValidatedEvidence` from `src/forgeops/evidence.py` and has no collection dependency.

`src/forgeops/cli.py` exposes the separate `evidence compare` path. It validates both inputs completely before rendering and does not construct `KubectlRunner`, `HttpRunner`, or `Collector`.

The repository-local distribution advances to `0.5.0`. `pyproject.toml` and `src/forgeops/__init__.py` remain synchronized; no distribution is published.

## Testing strategy

Focused synthetic coverage includes:

- timestamp-only equivalence;
- status regression and recovery semantics;
- same-status evidence changes;
- added and removed check identifiers;
- stable identifier ordering and byte-stable text rendering;
- reversed chronology;
- invalid second input producing no partial output;
- path and artifact-content redaction in diagnostics;
- proof that comparison constructs no collection or network runner;
- installed command help and an equivalent-artifact invocation; and
- regression coverage for existing snapshot and validation behavior.

All tests use repository fixtures or temporary files. No test invokes kubectl, contacts a network, accesses SignalForge, or mutates an artifact.

Local validation passes all 57 focused ForgeOps tests and all 115 repository tests. Kubernetes manifest validation, isolated package installation, installed `foundry-check`, `forgeops snapshot`, `forgeops evidence validate`, and `forgeops evidence compare` checks, and whitespace validation also pass.

## Documentation reconciliation

Milestone 048 first records the Gate 10 facts left intentionally pending when Milestone 047 closeout was written:

- closeout PR #34 merged at `2ebaa902f56f6b143009c4e630ba95f4a03759d8`;
- Gate 10 completed;
- both Milestone 047 branches were deleted locally and remotely;
- Milestone 047 is fully closed; and
- Milestone 048 is the immediate next step.

## Release and deployment impact

- Local package metadata only: `0.5.0`.
- No registry package, image, release tag, manifest, or deployed workload.
- No ServiceAccount, RBAC, Service, configuration, or persistent-state change.
- No deployment, rollout, restart, live acceptance, or Wiki change.

## Deterministic local acceptance

1. The branch begins at exact baseline `2ebaa902f56f6b143009c4e630ba95f4a03759d8`.
2. Equivalent validated artifacts with different timestamps return comparison exit code `0`.
3. Any added, removed, status-changed, or evidence-changed check returns comparison exit code `1`.
4. Invalid input or reversed chronology returns exit code `2` without partial comparison output.
5. Repeated rendering of the same comparison produces identical text.
6. Comparison never constructs or invokes collection, subprocess, or HTTP runners.
7. Diagnostics omit input paths and artifact contents.
8. Existing snapshot and evidence-validation tests remain compatible.
9. Focused ForgeOps tests, the complete repository suite, installed CLI checks, and whitespace validation pass.
10. The diff contains no image, manifest, deployment, Wiki, or cluster change.

## Rollback

Rollback is a focused source, tests, workflow, and documentation revert. The snapshot and `forgeops.snapshot/v1alpha1` contracts remain unchanged, so no artifact migration exists. No cluster, image, or persistent-state rollback is required.

## Relationship to later ForgeOps reasoning

The immutable comparison model gives later replay or reasoning work a bounded change set with check identifiers and explicit before/after statuses. A future reasoning layer may consume that model, but it must not automatically receive kubeconfig access, collection authority, broader Kubernetes permissions, network discovery, storage authority, or mutation capability.

Future explanations must distinguish observed changes from inferred causes, cite the check identifiers used, disclose uncertainty, and preserve human approval for operational action.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete.
3. Publication and draft PR — not authorized.
4. Package or image release — not applicable and not authorized.
5. Deployment — not applicable and not authorized.
6. Live acceptance — not applicable; acceptance is offline.
7. Pull-request readiness — not authorized.
8. Merge — not authorized.
9. Closeout — not authorized.
10. Branch cleanup — not authorized.
