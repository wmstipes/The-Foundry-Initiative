# Milestone 049 — ForgeOps deterministic JSON comparison contract

**Status:** Local implementation, draft PR publication, and CI complete; package/image release is closed as not applicable, and later gates remain separately gated

**Started:** 2026-09-17

**Implementation branch:** `codex/milestone-049-forgeops-json-comparison`

**Baseline:** `main` at `9055ef8d564809dd355f8cdfa175259c5b9ee677`

## Goal

Expose the existing immutable offline evidence comparison as a deterministic, disclosure-minimized JSON contract for scripts, CI, demonstrations, and later bounded reasoning consumers without adding collection, storage, diagnosis, or mutation authority.

## Audience

- SignalForge operators using offline scripts or CI.
- Developers building later scenario and evidence-grounded reasoning consumers.
- Technical reviewers evaluating contract design and least-authority architecture.

## Delivered interface

~~~powershell
forgeops evidence compare `
  --before .\forgeops-snapshot-before.json `
  --after .\forgeops-snapshot-after.json `
  --format json
~~~

`text` remains the default. Both formats derive from the same immutable `EvidenceComparison`, and the existing comparison exit semantics remain unchanged.

## JSON contract

The versioned schema is `forgeops.comparison/v1alpha1`. Fixed top-level fields are:

1. `schema`
2. `evidenceSchema`
3. `beforeCollectedAtUtc`
4. `afterCollectedAtUtc`
5. `beforeOverallStatus`
6. `afterOverallStatus`
7. `summary`
8. `deltas`
9. `limitations`

The summary records total, unchanged, and changed check counts; counts for each delta kind; and the comparison exit code. Every delta contains fixed `id`, `kind`, `beforeStatus`, `afterStatus`, and `changedFields` fields. Missing statuses serialize as `null`; added and removed checks use an empty changed-field array. Deltas retain the comparison model's stable identifier order.

The contract does not reproduce observation text, expected or observed values, evidence sources, error text, artifact paths, or complete source artifacts. It establishes deterministic representation, not provenance, authenticity, health, severity, causation, diagnosis, or recommendation.

## Trust boundary

The one-way authority path remains:

```text
validated evidence artifacts
→ immutable deterministic comparison
→ text or JSON rendering
→ optional future consumer
```

The JSON renderer accepts only `EvidenceComparison`. It cannot open source artifacts, construct a collector or runner, access kubeconfig, invoke a subprocess, contact a network, discover resources, persist output automatically, or mutate state. A later consumer receives no Kubernetes credentials, collection authority, broader RBAC, network-discovery capability, storage authority, or remediation capability through this contract.

## Explicit exclusions

- No comparison-document loader or validator.
- No input-schema compatibility negotiation.
- No scenario manifest, corpus, replay command, or history.
- No automatic output file creation or retention.
- No hashing, signing, attestation, or provenance claim.
- No trend analysis, causal inference, severity score, runbook mapping, diagnosis, or recommendation.
- No retrieval, model invocation, or AI reasoning.
- No new Kubernetes or HTTP source.
- No registry package, image, release tag, manifest, deployment, live acceptance, or Wiki change.
- No remediation or mutation.

## Implementation

`src/forgeops/comparison.py` owns the `forgeops.comparison/v1alpha1` renderer and comparison limitation statement. `src/forgeops/cli.py` adds the backward-compatible `--format text|json` selection to the existing command. `text` remains the default and uses the unchanged text renderer.

The repository-local distribution advances to `0.6.0`. `pyproject.toml` and `src/forgeops/__init__.py` remain synchronized; no distribution is published.

## Testing strategy

Offline tests cover:

- a fixed golden JSON document and repeated byte equality;
- exact top-level, summary, and delta field ordering;
- text/JSON timestamps, status, delta-count, and exit-code parity;
- all four delta kinds in stable identifier order;
- explicit `null` statuses and empty changed-field arrays;
- omission of paths and underlying evidence values;
- complete JSON with exit `1` for valid differences;
- no partial JSON for invalid input;
- no construction of collection or network runners; and
- preservation of snapshot, validation, comparison-text, and `foundry-check` behavior.

All fixtures are synthetic and all acceptance remains offline. No test invokes kubectl, contacts a network, accesses SignalForge, or mutates an artifact.

Local validation passes all 64 focused ForgeOps tests and all 122 repository tests. Isolated installation of `foundry-check==0.6.0`, installed `foundry-check`, `forgeops snapshot`, `forgeops evidence validate`, and text and JSON `forgeops evidence compare` checks, Kubernetes manifest validation, and whitespace validation also pass.

## Release and deployment impact

- Local package metadata only: `0.6.0`.
- No registry package, image, release tag, manifest, or deployed workload.
- No ServiceAccount, RBAC, Service, configuration, or persistent-state change.
- Gate 4 is explicitly closed as not applicable; `0.6.0` remains repository-local metadata and no registry distribution, image, or release tag was published.
- Gates 5–6 remain separately gated and are expected to be not applicable.
- No deployment, rollout, restart, live acceptance, or Wiki change.

## Publication evidence

- Draft PR: #37.
- Published branch: `codex/milestone-049-forgeops-json-comparison`.
- Accepted local implementation commit: `b35ffaeebde90421ea12274649baca2f2770f95d`.
- Published remote implementation commit: `c1501c4f3834c59d010b9ee1c68190c4b490947d`.
- Exact matching local and published tree: `80f08b91f755d9fc97a24a3dcd64f56c413cdb58`.
- The GitHub repository connector was used because this runtime's HTTPS Git client has no credential helper.
- ForgeOps CI run `35227321405` completed successfully on the published implementation tree.
- The PR remains draft. Package/image release is explicitly closed as not applicable; deployment, live acceptance, readiness, merge, closeout, and cleanup remain separately gated.

## Deterministic acceptance

1. The branch begins at exact baseline `9055ef8d564809dd355f8cdfa175259c5b9ee677`.
2. Milestone 048 closeout PR #36, Gate 10, deleted branches, full closure, and Milestone 049 sequencing are reconciled first.
3. Default comparison text remains compatible and `--format json` is explicit.
4. Repeated JSON rendering of one comparison is byte-identical.
5. JSON and text preserve identical timestamps, statuses, deltas, counts, and comparison exit semantics.
6. Timestamp-only differences remain equivalent.
7. All four delta kinds serialize in stable identifier order with explicit absence values.
8. Invalid input or chronology emits no partial comparison document.
9. Output omits artifact paths and underlying evidence values.
10. Comparison constructs no collector, subprocess runner, or network runner.
11. Focused and complete repository test suites pass.
12. Isolated installation and all installed command entry checks pass.
13. Kubernetes manifest and whitespace validation pass.
14. The diff contains no application, Kubernetes, Wiki, deployment, or cluster change.

## Rollback

Rollback removes the JSON comparison renderer and `--format` selection, restores repository-local package metadata to `0.5.0`, and retains the existing text comparison and snapshot artifact contract. Any redirected JSON is an operator-owned local file. No artifact migration, cluster rollback, image rollback, or persistent-data recovery is required.

## Relationship to later reasoning

The comparison JSON is a bounded machine-consumable handoff for a separately planned scenario or reasoning layer. A future consumer may cite check identifiers and observed change classifications, but it must distinguish facts from inference, disclose uncertainty, and gain no collection or mutation authority implicitly.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete.
3. Publication and draft PR — approved and complete through draft PR #37.
4. Package or image release — explicitly closed as not applicable; no distribution, image, or release tag was published.
5. Deployment — not authorized; expected to be not applicable.
6. Live acceptance — not authorized; expected to be not applicable.
7. Pull-request readiness — not authorized.
8. Merge — not authorized.
9. Closeout — not authorized.
10. Branch cleanup — not authorized.
