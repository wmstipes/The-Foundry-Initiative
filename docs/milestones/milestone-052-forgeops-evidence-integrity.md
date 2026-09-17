# Milestone 052 — ForgeOps deterministic evidence integrity records

**Status:** Implementation merged through PR #43 at `b4f42c24cb3afd3b4420716038d508a9f60712c3`; documentation-only closeout in progress

**Started:** 2026-09-17

**Implementation branch:** `codex/milestone-052-forgeops-evidence-integrity`

**Baseline:** clean `main` at `fd8187697dc472e2d3c39f2202636412a551b728`

## Goal

Detect exact-byte changes to one contract-valid ForgeOps evidence artifact by
creating and later verifying a deterministic SHA-256 sidecar record.

This milestone provides integrity relative to a separately retained trusted
record. It does not provide authorship, cryptographic authenticity, trusted
time, signing, attestation, storage history, or chain of custody.

## Interface

~~~powershell
forgeops evidence integrity create --input .\forgeops-snapshot.json

forgeops evidence integrity verify `
  --input .\forgeops-snapshot.json `
  --record .\forgeops-snapshot.integrity.json
~~~

Creation writes deterministic `forgeops.integrity/v1alpha1` JSON to standard
output. ForgeOps does not choose a retention location or automatically persist
the record. Verification reports only whether length, digest, and bounded
metadata match; it does not expose input paths or evidence values.

## Contract and semantics

The record contains, in fixed order:

- integrity schema;
- evidence schema;
- evidence collection timestamp;
- exact SignalForge context;
- `sha256` algorithm identifier;
- lowercase SHA-256 digest;
- exact evidence byte length; and
- the integrity limitation statement.

ForgeOps reads the evidence once, validates the supported snapshot contract,
and retains those exact bytes for hashing. This avoids validating one read and
hashing a later read of a file that might have changed between operations.

Creation exits `0` after rendering a valid record and `2` for invalid or
unreadable evidence. Verification exits `0` for a match, `1` for valid inputs
that do not match, and `2` for invalid or unreadable evidence or records.

## Trust boundary

A matching record is meaningful only when the operator retained the record
separately and trusts it. An actor able to replace both evidence and record can
produce a new matching pair. The digest is therefore not an authenticity,
identity, signature, attestation, timestamp, or chain-of-custody mechanism.

The component may read one explicit evidence file and one explicit integrity
record. Evidence remains bounded by 1 MiB; the record is bounded by 64 KiB. It
does not access a kubeconfig, invoke kubectl, contact HTTP or another network,
discover files, retain history, or mutate state.

## Testing strategy

Offline tests prove:

- exact, repeated rendering matches a fixed golden record;
- the evidence is validated before a record is created;
- unchanged exact bytes verify with exit `0`;
- a valid byte-only change returns mismatch exit `1`;
- malformed, duplicate-key, oversized, wrong-schema, wrong-algorithm, invalid
  digest, and invalid-length records fail closed;
- invalid inputs produce no partial standard output or sensitive paths;
- verification output omits evidence values; and
- integrity commands never construct collection or network runners.

## Explicit exclusions

- No signing key, certificate, identity provider, trusted timestamp, remote
  transparency log, attestation service, or chain-of-custody claim.
- No automatic record file creation, retention, upload, sharing, history, or
  database.
- No comparison change, scenario replay, runbook mapping, diagnosis,
  recommendation, retrieval, model invocation, AI reasoning, or remediation.
- No collection expansion, kubeconfig, kubectl, HTTP, network, image, manifest,
  deployment, cluster access, endpoint access, persistent-state change, or Wiki
  mutation.

## Release and deployment impact

- Repository-local package metadata advances from `0.7.0` to `0.8.0`.
- No package, image, release tag, or other registry artifact is published.
- No deployment or live acceptance is applicable; all acceptance remains
  offline.

## Publication evidence

- Accepted local implementation commit:
  `181a8d762925f2620595f03ad927424cd5f06ac1`.
- Published implementation commit:
  `912468e566086a5234339ac09b3f98dddc53b4a2`.
- Exact matching accepted and published tree:
  `eeb97ba2a7442353116cef90f9d77df180b02c48`.
- Draft PR #43 was opened from the published branch.
- ForgeOps CI run `35288211586` completed successfully.
- PR #43 was marked ready and merged at
  `b4f42c24cb3afd3b4420716038d508a9f60712c3`.
- The merge commit resolves to exact accepted tree
  `eeb97ba2a7442353116cef90f9d77df180b02c48`.
- The repository connector was used because this runtime's HTTPS Git client has
  no credential helper.

## Local acceptance

- All 87 focused ForgeOps tests pass.
- All 145 repository tests pass.
- An isolated non-editable `foundry-check==0.8.0` installation reports matching
  distribution and module versions and successfully creates and verifies the
  golden integrity record.
- The repository-owned source launcher reports the current checkout and also
  creates and verifies an exact-byte record.
- Installed command entry checks, Python compilation, Kubernetes manifest
  validation, and whitespace validation pass.
- No SignalForge, Kubernetes API, application endpoint, or other network target
  was accessed.

## Gated delivery workflow

1. Planning — pre-approved and complete.
2. Local implementation — pre-approved and complete; deterministic offline acceptance passes.
3. Publication and draft PR — pre-approved and complete through PR #43 with exact-tree verification.
4. Package or image release — approved disposition: not applicable.
5. Deployment — approved disposition: not applicable.
6. Live acceptance — approved disposition: not applicable.
7. Pull-request readiness — pre-approved and complete after successful CI and exact-tree review.
8. Merge — pre-approved and complete; PR #43 merged at `b4f42c24cb3afd3b4420716038d508a9f60712c3`.
9. Closeout — pre-approved and in progress through `codex/milestone-052-closeout`.
10. Branch cleanup — pre-approved and pending closeout merge verification.
