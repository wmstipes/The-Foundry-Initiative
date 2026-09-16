# Milestone 046 — ForgeOps deterministic JSON evidence contract

**Status:** Local implementation, offline validation, publication, draft PR, and CI complete; live acceptance and later gates remain separately gated

**Started:** 2026-09-16

**Branch:** `codex/milestone-046-forgeops-json-evidence`

## Goal

Formalize the existing evaluated `forgeops.snapshot/v1alpha1` model as a deterministic, redacted JSON artifact for operators, automated consumers, portfolio review, and later evidence-grounded ForgeOps capabilities without expanding collection or mutation authority.

## Why this increment

Milestone 045 established a bounded collector and deterministic evaluator, but exposed results only as terminal and Markdown views. Adding more Kubernetes sources would widen the trust boundary, while recommendations or AI reasoning would introduce interpretation before ForgeOps had a stable machine-readable handoff. Snapshot comparison is useful but depends on such an artifact.

Milestone 046 therefore adds the smallest useful integration surface: a JSON view of the already evaluated snapshot.

## Scope

- Add `json` to the existing `forgeops snapshot --format` choices.
- Serialize schema, collection time, requested context, fixed scope, redaction statement, summary, ordered checks, and limitations.
- Preserve the evaluator's status precedence and process exit code.
- Include optional expected, observed, and error-category fields only when present.
- Guarantee byte-stable output when the same evaluated model is rendered more than once.
- Advance local package metadata from `0.2.0` to `0.3.0`.
- Reconcile repository documentation with completed Milestone 045 closeout and cleanup evidence.

## Explicit exclusions

- No new Kubernetes or HTTP data sources.
- No raw Kubernetes objects or HTTP responses in JSON.
- No logs, Events, Secrets, ConfigMaps, RBAC contents, broad discovery, or arbitrary paths.
- No snapshot input, replay, comparison, history, retention, automatic file writing, signing, or attestation.
- No diagnosis, recommendation, runbook selection, retrieval, language model, or AI reasoning.
- No package registry, image, tag, manifest, deployment, Wiki, or cluster mutation.

## Trust and safety boundary

The Milestone 045 boundary remains authoritative. Exact kubeconfig and context targeting, the closed operation enum, fixed resource identities and selectors, explicit optional HTTP URLs, timeouts, output limits, redirect rejection, selected-field normalization, redaction, and fail-closed `UNKNOWN` handling are unchanged.

The JSON renderer accepts only an `EvaluatedSnapshot` and a text stream. It cannot invoke kubectl, contact HTTP endpoints, read a kubeconfig, write a file independently, or recover any field discarded during normalization. Standard output remains the only application output path; saving an artifact requires explicit operator redirection.

## JSON contract

Top-level fields have a fixed order:

1. `schema`
2. `collectedAtUtc`
3. `context`
4. `scope`
5. `redaction`
6. `summary`
7. `checks`
8. `limitations`

The summary contains `pass`, `warn`, `fail`, `unknown`, `overallStatus`, and `exitCode`. Checks retain evaluator order and contain `id`, `status`, `observation`, `source`, and `collectedAtUtc`, followed by applicable optional detail fields.

Determinism applies to serialization: the same `EvaluatedSnapshot` produces the same UTF-8-compatible, indented JSON bytes with one final newline. Separately collected snapshots may differ by timestamp or observed state.

## Testing strategy and local evidence

The offline suite covers:

- fixed golden JSON bytes;
- repeat-render byte equality;
- JSON parsing and fixed ordered check identities;
- terminal, Markdown, and JSON status parity;
- summary and exit-code parity;
- combined WARN, FAIL, and UNKNOWN precedence;
- omission of optional fields when absent;
- absence of explicit HTTP addresses and kubeconfig paths;
- explicit CLI acceptance and offline end-to-end rendering of `--format json`; and
- all prior collection, evaluation, runner, timeout, allowlist, and redaction regressions.

Local validation result: 33 ForgeOps tests and all 91 repository tests passed, and `git diff --check` passed. Tests use only synthetic fixtures; they do not invoke kubectl or contact a network.

## Release and deployment impact

The repository-local Python distribution version becomes `0.3.0`. No package is published to a registry, and no image or tag is built. There are no Kubernetes manifests, ServiceAccounts, RBAC objects, workloads, configuration changes, rollouts, restarts, or persistent-state changes.

## Publication evidence

- Draft PR: #31.
- Published branch: `codex/milestone-046-forgeops-json-evidence`.
- Reviewed local commit: `e097b78a358bd10f23c36e2f1706bfdc3445737c`.
- Published remote commit: `2f49025698b5a54b2d863adba4b2192e0a88579f`.
- Exact matching local and published tree: `0f4ac04483b36615a5848cd940b8457203d40c5a`.
- The GitHub repository connector was used because this runtime's HTTPS Git client had no credential helper.
- ForgeOps CI run `35136846722` completed successfully after the publication-evidence follow-up.
- The PR remains draft; live acceptance, readiness, merge, closeout, and cleanup are not authorized.

## Acceptance plan

After publication is separately approved, CI must install the exact branch, pass the complete offline ForgeOps suite, and expose JSON in both command entry points. A later separately approved live acceptance may run the exact published commit against the existing bounded SignalForge target, redirect JSON to an operator-selected local file, parse it, confirm the expected schema and 33-check healthy baseline, and search it for prohibited data. That acceptance must use only the existing read allowlist and five explicit HTTP GETs and must not mutate the cluster.

## Documentation

- README: JSON invocation and renderer parity.
- Roadmap: Milestone 045 cleanup reconciliation and Milestone 046 scope.
- Architecture: JSON presentation boundary and updated live-acceptance state.
- Project status: current local implementation and next approval gate.
- Learning journal: decision, implementation, validation, and lesson.
- Snapshot runbook: safe JSON redirection and interpretation.
- This record: scope, boundaries, evidence, gates, and rollback.

Kubernetes documentation is unchanged because Milestone 046 introduces no Kubernetes resource or operating procedure.

## Rollback

Rollback is a normal source revert of the focused implementation. Removing the JSON renderer and CLI choice restores the Milestone 045 interface; text and Markdown behavior require no migration. No cluster rollback, persistent-data recovery, image rollback, or deployment action is needed. Any redirected JSON file is an operator-owned local artifact and is not automatically removed.

## Relationship to later ForgeOps reasoning

The artifact establishes a one-way interface from bounded collection through deterministic evaluation to a versioned evidence representation. A future comparison, replay, or reasoning component may consume that artifact, but it must not receive collection credentials, expand the allowlist, reinterpret missing evidence as healthy, or gain mutation authority implicitly. Future diagnoses and recommendations must remain distinguishable from evidence and cite the check identifiers they use.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete.
3. Publication and draft PR — approved and complete through draft PR #31.
4. Package or image release — not applicable and not authorized.
5. Deployment — not applicable and not authorized.
6. Live acceptance — not authorized.
7. Pull-request readiness — not authorized.
8. Merge — not authorized.
9. Closeout — not authorized.
10. Branch cleanup — not authorized.
