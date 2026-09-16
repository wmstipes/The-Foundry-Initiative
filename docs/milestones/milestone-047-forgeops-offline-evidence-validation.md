# Milestone 047 — ForgeOps deterministic offline evidence validation

**Status:** Local implementation, draft PR publication, and CI complete; PR readiness and later gates remain separately gated

**Started:** 2026-09-16

**Branch:** `codex/milestone-047-forgeops-evidence-validation`

**Baseline:** `main` at `66bae40d7d0a6d706db47db54a0335de1d93a22f`

## Goal

Add a strict offline compatibility gate for one operator-supplied `forgeops.snapshot/v1alpha1` JSON artifact before comparison, replay, runbook mapping, or future reasoning consumes it.

The validator must distinguish artifact validity from contained health, fail closed on malformed or inconsistent input, and preserve the established one-way authority boundary:

```text
bounded collection
→ selected-field normalization
→ deterministic evaluation
→ redacted evidence artifact
→ strict offline validation
→ optional future reasoning
```

## Audience

- The SignalForge operator retaining or sharing a saved evidence artifact.
- Developers building later ForgeOps evidence consumers.
- Technical reviewers evaluating contract, privacy, and safety discipline.

## Why this is the smallest useful increment

Milestone 046 created a deterministic JSON handoff, but the repository had no reusable consumer that could reject unsupported schemas, duplicate keys, malformed field sets, or a summary that disagreed with its checks. Implementing comparison first would have embedded an incomplete parser inside a larger feature. Replay would require a new pre-evaluation evidence model, and AI reasoning would add nondeterministic interpretation before the input boundary was enforced.

Milestone 047 therefore adds only the reusable ingestion gate. It does not derive a new operational conclusion.

## Delivered interface

~~~powershell
forgeops evidence validate `
  --input .\forgeops-snapshot.json
~~~

The equivalent module entry point is also available:

~~~powershell
python -m forgeops evidence validate `
  --input .\forgeops-snapshot.json
~~~

A valid artifact produces one deterministic line:

~~~text
VALID forgeops.snapshot/v1alpha1 checks=<count> containedOverall=<status> containedExit=<code>
~~~

Validator exit code `0` means the artifact satisfies the supported contract. The contained status may still be `WARN`, `FAIL`, or `UNKNOWN`. Validator exit code `2` means the input is unreadable, oversized, malformed, unsupported, or internally inconsistent.

## Input and compatibility boundary

- Read exactly one explicitly selected regular file.
- Read no more than 1 MiB.
- Require UTF-8 JSON.
- Reject duplicate object keys and non-standard numeric constants.
- Require the exact `forgeops.snapshot/v1alpha1` schema.
- Require the reviewed top-level, summary, and per-check field order.
- Reject missing, unexpected, reordered, or incorrectly typed fields.
- Require second-precision RFC 3339 UTC timestamps and matching per-check collection times.
- Require non-empty, unique check identifiers and supported status values.
- Require the exact scope, redaction, and limitation statements.
- Recalculate status counts, overall-status precedence, and contained exit code from the checks.
- Return an immutable validated representation for later separately planned consumers.

The validator does not prove provenance, cryptographic authenticity, continuous health, or that arbitrary string values contain no sensitive text. Operators must still review an artifact before sharing it.

## Explicit exclusions

- No kubeconfig input, search, or fallback.
- No kubectl, subprocess, HTTP, DNS, or other network activity.
- No Kubernetes or application collection.
- No additional resource, log, Event, Secret, ConfigMap, or telemetry source.
- No artifact repair, rewrite, copy, deletion, retention, history, signing, or attestation.
- No comparison, replay, runbook mapping, diagnosis, recommendation, retrieval, language model, or AI reasoning.
- No package registry, image, tag, manifest, deployment, Wiki, or cluster action.
- No mutation authority.

## Implementation

`src/forgeops/evidence.py` owns the bounded file read, duplicate-key JSON decoding, contract checks, semantic summary recalculation, and immutable `ValidatedEvidence` result. It accepts only serialized evaluated evidence and cannot recover raw Kubernetes or HTTP responses.

`src/forgeops/cli.py` exposes the separate `evidence validate` path. That path does not construct `KubectlRunner`, `HttpRunner`, or `Collector`. Existing `snapshot` behavior and its exit semantics remain unchanged.

The repository-local distribution advances to `0.4.0`. `pyproject.toml` and `src/forgeops/__init__.py` are synchronized; no distribution is published.

## Testing strategy

Focused offline coverage includes:

- the fixed golden artifact;
- valid unhealthy evidence returning validator success while preserving contained `UNKNOWN`;
- proof that no collection or network runner is constructed;
- duplicate JSON keys;
- non-UTF-8 input and non-standard numeric constants;
- input larger than 1 MiB;
- unsupported schema;
- reordered or unexpected fields;
- incorrect optional-field order;
- mismatched timestamps;
- duplicate check identifiers;
- incorrect summary counts, overall status, or contained exit code;
- boolean values rejected as integer counts;
- missing file and directory input; and
- diagnostics that omit the operator-supplied path.

All tests use repository fixtures or temporary local files. No test invokes kubectl, contacts a network, or accesses SignalForge.

Local validation currently passes 48 focused ForgeOps tests and all 106 repository tests.

## Documentation reconciliation

Milestone 047 first reconciles the four records intentionally left before Gate 10 completed:

- Milestone 046 closeout PR #32 merged at `66bae40d7d0a6d706db47db54a0335de1d93a22f`.
- Gate 10 completed.
- Both Milestone 046 branches were deleted locally and remotely.
- Milestone 046 is fully closed.
- Milestone 047 is the immediate next step.

It also corrects the README ForgeOps renderer summary, the stale Workbench `0.5.1` reference in `k8s/README.md`, and the stale ForgeOps module version.

## Release and deployment impact

- Local package metadata only: `0.4.0`.
- No registry package or release tag.
- No container image.
- No application or Kubernetes manifest.
- No ServiceAccount, RBAC, Service, workload, configuration, or persistent-state change.
- No deployment, rollout, restart, or live acceptance.
- No Wiki source or live Wiki change.

## Publication evidence

- Draft PR: #33.
- Published branch: `codex/milestone-047-forgeops-evidence-validation`.
- Reviewed local commit: `bab4f3cb93d591729614927de57a7791cb856452`.
- Published remote commit: `e848bed96a57cb62ab6fad6289a9310f52758ca0`.
- Exact matching local and published tree: `e0e078a3bb7c87970ec070a951b5e3779c12b5a2`.
- The GitHub repository connector was used because this runtime's HTTPS Git client had no credential helper.
- ForgeOps CI run `35155205132` and Kubernetes Manifest Validation run `35155205187` completed successfully on published documentation head `bdbe35deae629e1af5451a7a51966464eb6cea6e`.
- The PR remains draft. PR readiness, merge, closeout, and cleanup remain separately gated.

## Deterministic local acceptance

1. The branch begins at exact baseline `66bae40d7d0a6d706db47db54a0335de1d93a22f`.
2. A repeated golden-artifact validation produces the same one-line result.
3. A valid `UNKNOWN` artifact returns validator exit code `0` and reports contained exit code `2`.
4. Malformed, duplicate-key, oversized, unsupported, and inconsistent inputs fail closed with validator exit code `2`.
5. Validation does not construct or call collection, subprocess, or HTTP runners.
6. Diagnostics omit the input path and artifact contents.
7. Existing snapshot renderers and `foundry-check` remain compatible.
8. Focused ForgeOps tests, the complete repository suite, installed CLI checks, and whitespace validation pass.
9. The diff contains no image, manifest, deployment, Wiki, or cluster change.

## Rollback

Rollback is a focused source-and-documentation revert. The `forgeops snapshot` command and the `forgeops.snapshot/v1alpha1` artifact remain unchanged, so no evidence migration is required. No cluster, image, or persistent-state rollback exists.

## Relationship to later ForgeOps reasoning

This validator becomes the only approved input seam for later evidence consumers. A future comparison or reasoning component may receive `ValidatedEvidence`, but it must not automatically receive kubeconfig access, collection authority, broader Kubernetes permissions, network discovery, storage authority, or mutation capability.

Future diagnoses and recommendations must remain separate from evidence, cite the check identifiers used, disclose uncertainty, and preserve human approval for operational action.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete.
3. Publication and draft PR — approved and complete through draft PR #33.
4. Package or image release — not applicable and not authorized.
5. Deployment — not applicable and not authorized.
6. Live acceptance — not applicable; acceptance is offline.
7. Pull-request readiness — not authorized.
8. Merge — not authorized.
9. Closeout — not authorized.
10. Branch cleanup — not authorized.
