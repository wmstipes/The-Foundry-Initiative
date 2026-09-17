# Milestone 050 — ForgeOps bounded synthetic scenario corpus

**Status:** Implementation merged through PR #39 at `090a47f7cd546f4d2c0dac952da387f4e1fdf863`; documentation-only closeout in progress

**Started:** 2026-09-17

**Implementation branch:** `codex/milestone-050-forgeops-scenario-corpus`

**Baseline:** local reconciliation commit `ff17c446a21ff44422ddd25b78853a755eed5c2f`, based on `main` at `38bf1d84d5ad0611d050e1825233af82f369b4af`

## Goal

Create a small, deterministic, disclosure-minimized corpus that demonstrates stable evidence, regressions, incomplete evidence, and recovery through the existing ForgeOps offline validation and comparison seams.

The corpus extends the evaluation path without expanding the authority path:

```text
synthetic redacted evidence artifacts
→ strict offline validation
→ deterministic offline comparison
→ exact deterministic comparison representation
→ optional future evaluation consumer
```

## Audience

- The SignalForge operator demonstrating ForgeOps behavior without accessing the lab.
- Developers extending ForgeOps validation, comparison, or later reasoning.
- Technical and portfolio reviewers evaluating deterministic, least-authority incident tooling.

## Why this is the smallest useful increment

Milestones 047-049 established strict evidence ingestion, immutable comparison, and a machine-readable comparison contract. Existing tests prove individual edge cases, but most comparison cases construct small mutations inside test code. A checked-in scenario corpus makes regression and recovery behavior directly reviewable and reusable before runbook mapping or AI-assisted reasoning is introduced.

Adding a replay command, comparison-document loader, provenance system, compatibility layer, or reasoning component would add production behavior before a representative offline evaluation set existed. Milestone 050 therefore adds fixtures, exact expectations, tests, and documentation only.

## Scenario scope

The corpus contains five directories under `tests/fixtures/forgeops/scenarios`:

| Scenario | Before | After | Comparison exit |
| --- | --- | --- | ---: |
| `stable-baseline` | `PASS` | `PASS` | `0` |
| `pod-restart-warning` | `PASS` | `WARN` | `1` |
| `routing-regression` | `PASS` | `FAIL` | `1` |
| `incomplete-evidence` | `PASS` | `UNKNOWN` | `1` |
| `routing-recovery` | `FAIL` | `PASS` | `1` |

Each scenario includes valid `before.json` and `after.json` evidence plus exact expected comparison JSON. Each evidence artifact contains one isolated synthetic check so the named transition and expected changed fields are unambiguous. Its overall status applies only to that focused artifact and is not a complete health statement.

## Trust and privacy boundary

- All scenario data is intentionally synthetic.
- No artifact is derived from a live SignalForge snapshot or captured response.
- No real address, kubeconfig path, credential, token, UID, complete Kubernetes object, or private diagnostic is included.
- Inputs use the unchanged `forgeops.snapshot/v1alpha1` contract.
- Expected outputs use the unchanged `forgeops.comparison/v1alpha1` contract.
- Validation and comparison remain offline and construct no collector, kubectl runner, or HTTP runner.
- A comparison exit of `1` means valid artifacts differ. It does not establish failure, severity, causation, or diagnosis; a valid recovery also returns `1`.
- The corpus is evaluation data, not training data, current-health evidence, provenance, attestation, diagnosis, recommendation, or remediation.

## Explicit exclusions

- No new production model, schema, or compatibility rule.
- No new CLI, scenario runner, replay engine, or comparison-document loader.
- No collection source, kubeconfig access, kubectl operation, HTTP request, network discovery, or expanded allowlist.
- No real evidence, raw Kubernetes object, log, Event, Secret, ConfigMap, or telemetry expansion.
- No artifact repair, rewrite, automatic retention, history, database, signing, hashing, attestation, or provenance claim.
- No severity scoring, causal inference, runbook mapping, diagnosis, recommendation, retrieval, model invocation, AI reasoning, remediation, or mutation.
- No package-version change, registry package, image, release tag, manifest, deployment, live acceptance, or Wiki change.

## Implementation

The scenario directories contain only static JSON fixtures and a README. `tests/test_forgeops_scenarios.py` owns the exact inventory and expectations. It loads every before/after artifact through `load_evidence_file`, compares validated representations through `compare_evidence`, renders JSON through `render_comparison_json`, and verifies exact expected bytes.

No source under `src/forgeops` changes. Repository-local package metadata remains `0.6.0`. The existing ForgeOps workflow already watches `tests/test_forgeops*.py` and `tests/fixtures/forgeops/**`, so no workflow expansion is required.

## Testing strategy

Focused offline coverage proves:

- the corpus contains exactly the five accepted scenarios and three files per scenario;
- every input artifact passes the strict existing validator;
- every scenario preserves the expected contained before and after status;
- the stable scenario ignores timestamp-only change and returns comparison exit `0`;
- warning, failure, incomplete-evidence, and recovery scenarios return comparison exit `1`;
- incomplete evidence retains contained `UNKNOWN` and contained exit `2`;
- recovery is represented as `FAIL` to `PASS` without converting comparison difference semantics into health semantics;
- delta identifier, kind, before/after status, and changed fields are exact;
- repeated JSON rendering is byte-identical and matches the checked-in expected document;
- the existing CLI validates and compares the corpus without constructing collection or network components; and
- a disclosure scan rejects representative address, credential, UID, and complete-object markers.

All tests use local fixtures. No test invokes kubectl, contacts a network, or accesses SignalForge.

Local acceptance passes all 68 focused ForgeOps tests and all 126 repository tests. An isolated `foundry-check==0.6.0` installation, all installed command entry points, stable and recovery scenario comparisons, Kubernetes manifest validation, and whitespace validation also pass.

## Deterministic acceptance

1. The branch begins at exact local reconciliation commit `ff17c446a21ff44422ddd25b78853a755eed5c2f`.
2. The pending Milestone 049 Gate 10 reconciliation remains intact in branch history.
3. Every scenario input passes strict offline validation.
4. Every comparison matches its expected JSON byte for byte.
5. Stable evidence returns comparison exit `0` with no deltas.
6. Regressions and recovery return comparison exit `1` with exact deltas.
7. Incomplete evidence retains contained `UNKNOWN` and exit `2` independently from comparison exit `1`.
8. Repeated rendering is byte-stable.
9. No collector, subprocess runner, or network runner is constructed.
10. Corpus content remains explicitly synthetic and disclosure-minimized.
11. Focused ForgeOps and complete repository test suites pass.
12. Isolated installation and existing installed command entry checks pass.
13. Kubernetes manifest and whitespace validation pass.
14. The diff contains no production ForgeOps source, package-version, workflow, application, Kubernetes, Wiki, deployment, or cluster change.

## Release and deployment impact

- Repository-local package metadata remains `0.6.0`.
- No distribution, image, release tag, manifest, deployed workload, ServiceAccount, RBAC, Service, configuration, or persistent state changes.
- No deployment, rollout, restart, live acceptance, cluster access, endpoint access, or Wiki change.
- Gates 4-6 were explicitly approved and closed as not applicable. No release, deployment, or live acceptance occurred.

## Documentation updates

- `README.md` introduces the corpus and its evaluation-only boundary.
- `ROADMAP.md` records Milestone 050 in Phase 6.
- `docs/architecture.md` records the synthetic evaluation layer above unchanged validation and comparison seams.
- `docs/project-status.md` records local implementation and the next approval boundary.
- `docs/learning-journal.md` records implementation and lessons.
- `docs/runbooks/forgeops-snapshot.md` provides offline scenario commands and interpretation guidance.
- The corpus README documents inventory, contents, and disclosure limitations.

## Rollback

Rollback removes the scenario fixtures, focused test module, and associated documentation. The production ForgeOps package, both JSON contracts, existing saved artifacts, and existing commands remain unchanged. No package, image, cluster, or persistent-state rollback exists.

## Relationship to later ForgeOps reasoning

The corpus is a future evaluation set, not training data. A later reasoning experiment can be tested for evidence citation, observed-versus-inferred separation, uncertainty handling, `UNKNOWN` behavior, and correct recovery interpretation before any broader capability is considered.

A future consumer must not automatically receive kubeconfig access, collection authority, broader Kubernetes permissions, network discovery, storage authority, or mutation capability. Diagnosis and recommendation remain separately planned capabilities requiring explicit grounding and human approval.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete; deterministic offline acceptance passes.
3. Publication and draft PR — approved and complete; PR #39 opened from published head `067af70ef568a7342a8af6218cb6cddd252d9894` with exact accepted tree `53f6de423608b1f6ca3a74b93b04b65f93d67051`.
4. Package or image release — approved disposition and closed as not applicable.
5. Deployment — approved disposition and closed as not applicable.
6. Live acceptance — approved disposition and closed as not applicable.
7. Pull-request readiness — approved and complete after successful ForgeOps CI run `35240317432`.
8. Merge — approved and complete; PR #39 merged at `090a47f7cd546f4d2c0dac952da387f4e1fdf863`, preserving accepted tree `53f6de423608b1f6ca3a74b93b04b65f93d67051`.
9. Closeout — approved and in progress on `codex/milestone-050-closeout`.
10. Branch cleanup — approved and pending closeout merge verification.
