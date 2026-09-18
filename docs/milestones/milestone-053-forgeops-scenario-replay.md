# Milestone 053 — ForgeOps bounded offline scenario replay

**Status:** Local implementation and deterministic offline acceptance complete

**Started:** 2026-09-18

**Implementation branch:** `codex/milestone-053-forgeops-scenario-replay`

**Baseline:** clean `main` at `801f8cedaf411361e3e02b47cdae217ee56959c5`

## Goal

Replay one explicitly selected offline scenario through the production evidence
validator and deterministic comparison seam, then check its actual immutable
comparison against one strictly validated expected comparison.

Replay evaluates deterministic software behavior. It does not establish
current health, evidence authenticity, operational severity, causation,
diagnosis, runbook applicability, recommendation, or remediation authority.

## Interface

~~~powershell
forgeops scenario replay `
  --before .\before.json `
  --after .\after.json `
  --expected .\expected-comparison.json
~~~

All three paths are mandatory and explicit. ForgeOps does not accept a scenario
directory, search for matching files, or discover additional scenarios.

## Validation and execution flow

1. Strictly load the before artifact through `forgeops.snapshot/v1alpha1`.
2. Strictly load the after artifact through the same evidence contract.
3. Strictly load the expected `forgeops.comparison/v1alpha1` document.
4. Reject reversed evidence chronology.
5. Produce the actual immutable comparison through `compare_evidence`.
6. Compare the actual and expected immutable models.
7. Render only a bounded match summary.

The new comparison loader enforces a 256 KiB maximum, UTF-8 standard JSON,
duplicate-key rejection, exact ordered fields, supported schemas, timestamps,
statuses and delta kinds, sorted unique delta identifiers, ordered changed
fields, kind-specific null/status shapes, exact limitation text, and
recalculated summary counts and comparison exit.

## Exit semantics

| Exit | Meaning |
| ---: | --- |
| `0` | The actual deterministic comparison exactly matches the validated expectation. |
| `1` | All inputs are valid, but actual and expected comparisons differ. |
| `2` | Evidence, expectation, or chronology is invalid or unreadable. |

Replay exit is independent of contained health and comparison exit. A valid
routing regression or recovery has comparison exit `1` but returns replay exit
`0` when that difference is exactly expected.

## Trust and authority boundary

- Input is limited to two explicit evidence files of at most 1 MiB each and one
  explicit expected comparison of at most 256 KiB.
- Output omits input paths, observations, expected or observed evidence values,
  sources, and check identifiers.
- Replay invokes no collector, kubectl runner, HTTP runner, network service,
  directory scan, model, or remediation path.
- Replay does not automatically verify Milestone 052 integrity records. An
  operator may separately verify a trusted record before replay.
- The checked-in corpus remains synthetic evaluation data, not captured
  SignalForge evidence or training data.

## Testing strategy

Offline tests prove:

- the command requires three explicit inputs;
- all five curated scenarios replay as exact expectation matches;
- regression, incomplete-evidence, and recovery comparisons retain comparison
  exit `1` while replay returns `0`;
- a valid but incorrect expected model returns replay exit `1`;
- malformed, oversized, duplicate-key, inconsistent-summary, and invalid-delta
  expected comparisons fail closed;
- an expected-comparison directory is rejected;
- errors and mismatch output disclose no input path or evidence identifier;
- invalid input produces no partial success output; and
- replay constructs no collection or network runner.

## Explicit exclusions

- No scenario discovery, directory input, batch runner, watch mode, history,
  retention, database, upload, or automatic persistence.
- No integrity or authenticity claim, signature, trusted time, attestation, or
  chain of custody.
- No runbook mapping, severity scoring, causal inference, diagnosis,
  recommendation, retrieval, model invocation, AI reasoning, remediation, or
  mutation.
- No package/image publication, release tag, manifest, deployment, live
  acceptance, cluster access, endpoint access, persistent-state change, or Wiki
  mutation.

## Release and deployment impact

- Repository-local package metadata advances from `0.8.0` to `0.9.0`.
- No distribution, image, or release tag is published.
- Deployment and live acceptance are not applicable; acceptance remains
  entirely offline.

## Local acceptance

- All 95 focused ForgeOps tests pass.
- All 153 repository tests pass.
- An isolated non-editable `foundry-check==0.9.0` installation reports matching
  distribution and module versions and successfully replays stable and recovery
  scenarios.
- The repository-owned source launcher reports the current checkout and
  successfully replays the incomplete-evidence scenario.
- Installed command entry checks, Python compilation, Kubernetes manifest
  validation, and whitespace validation pass.
- No SignalForge, Kubernetes API, application endpoint, or other network target
  was accessed.

## Gated delivery workflow

1. Planning — pre-approved and complete.
2. Local implementation — pre-approved and complete; deterministic offline acceptance passes.
3. Publication and draft PR — pre-approved and pending.
4. Package or image release — approved disposition: not applicable.
5. Deployment — approved disposition: not applicable.
6. Live acceptance — approved disposition: not applicable.
7. Pull-request readiness — pre-approved and pending successful CI and exact-tree review.
8. Merge — pre-approved and pending.
9. Closeout — pre-approved and pending.
10. Branch cleanup — pre-approved and pending merge verification.
