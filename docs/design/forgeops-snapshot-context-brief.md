# Snapshot context in incident briefs

**Status:** Implemented candidate for review, October 3, 2026.

**Baseline:** Main `b4d9673553133d55646fc2a80134bbc3f367a718`, after PRs
#169 and #170. This milestone improves the offline incident-copilot
demonstration and tests the trustworthiness of its conclusions.

## Problem and decision

The v1alpha1 brief retains only deltas. An unchanged failure can produce
STABLE, and one recovered check can produce RECOVERED while another remains
failed or unknown. A heading warning does not restore discarded context.

Add opt-in `forgeops.incident-brief/v1alpha2`, assembled from the two explicitly
supplied snapshots, comparison, and mapping. Preserve every supplied check ID
and status, both snapshot summaries, the original delta brief, coverage
changes, and a separate recovery assessment. No raw observations, HTTP bodies,
addresses, or new collection fields enter the brief.

~~~text
forgeops incident brief --brief-version v1alpha2 \
  --before before.json --after after.json \
  --comparison comparison.json --mapping mapping.json --format text

forgeops incident replay --brief-version v1alpha2 \
  --before before.json --after after.json \
  --comparison comparison.json --mapping mapping.json --expected brief.json
~~~

Omitting the version retains v1alpha1 behavior. Snapshot arguments are rejected
in v1alpha1 mode so they cannot be silently ignored. Both snapshots are required
in v1alpha2 mode. Replay expectations must match the explicitly selected
version; there is no implicit conversion of old evidence.

## Ordered JSON contract

| Field | Contents |
| --- | --- |
| `schema` | `forgeops.incident-brief/v1alpha2` |
| `evidenceSchema` | `forgeops.snapshot/v1alpha1` |
| `before`, `after` | Collection time, recomputed summary, sorted complete list of supplied check IDs and statuses |
| `coverage` | Fixed `NOT_ESTABLISHED` completeness, sorted added/removed check IDs, and a fixed explanation of absent evidence |
| `assessment` | Recovery classification, known recovered IDs, regained-evidence IDs, remaining non-passing IDs |
| `deltaBrief` | Unmodified v1alpha1 brief contract, including its explicitly delta-only state, facts, mapping, uncertainties and limitations |
| `limitations` | Fixed authority, coverage, linkage, and authenticity limitations |

Each snapshot context has exactly `collectedAtUtc`, `summary`, and `checks`.
Its summary has `pass`, `warn`, `fail`, `unknown`, `overallStatus`, and
`exitCode`; each check has only `id` and `status`. Check arrays are nonempty,
unique, and sorted. Overall status uses the existing UNKNOWN > FAIL > WARN >
PASS precedence, while separate counts and check statuses retain simultaneous
failure and uncertainty.

Coverage has exactly `completeness`, `addedCheckIds`, `removedCheckIds`, and
`limitations`. Assessment has exactly `recovery`, `knownRecoveredCheckIds`,
`regainedEvidenceCheckIds`, and `remainingNonPassingCheckIds`. Arrays are sorted
and recomputed from the retained checks, not accepted as independent assertions.

## Recovery and coverage rules

Known recovery means a common check changed from WARN or FAIL to PASS.
Regained evidence means a common check changed from UNKNOWN to a known status,
including WARN or FAIL. Newly added passing checks are neither kind of recovery.

| Recovery classification | Rule |
| --- | --- |
| `NONE_ESTABLISHED` | No known WARN/FAIL-to-PASS transition, including UNKNOWN-to-PASS alone |
| `PARTIAL` | Some known recovery occurred, but a non-passing check remains or the check identity set changed |
| `COMPLETE_FOR_SUPPLIED_CHECKS` | At least one known recovery, identical before/after ID sets, and every after check PASS |

Complete recovery is scoped to the supplied identities, never to the cluster
or application as a whole. A removed check, even a passing one, prevents that
classification. Added identities also make recovery partial. Known recovery
and regained evidence can coexist and are listed separately. Remaining WARN,
FAIL, and UNKNOWN checks are visible in text regardless of whether they changed.

The snapshot contract does not declare a complete expected evidence profile
or which optional HTTP groups were requested. Therefore completeness is always
NOT_ESTABLISHED. Checks absent from both artifacts are not assessed; HTTP and
mesh/path coverage cannot be inferred from an empty delta list. The new format
does not invent an omitted-check identity or explain why evidence is missing.

## Validation and trust boundary

Construction strictly loads all four files and recomputes the comparison from
the source snapshots. Every comparison field must match, including chronology,
aggregate statuses, IDs, counts, kinds, and changed fields. Existing mapping
linkage validation then checks the window and delta reasons.

The new loader rejects duplicate keys, unsupported versions, unknown/reordered
fields, malformed types, numeric booleans, unsorted/duplicate IDs, inconsistent
summaries, false assessment or coverage claims, missing status/addition/removal
facts, incompatible delta facts, and reversed chronology. Nested delta briefs
also pass the existing strict v1alpha1 parser. Serialized input/output is bounded
to 1 MiB; the nested brief retains its existing 256 KiB limit. Failure produces
exit 2 without partial output or input path disclosure. Valid brief generation
returns 0 regardless of health; replay returns 0 for match and 1 for mismatch.

A saved brief alone cannot recheck the raw fields behind EVIDENCE_CHANGED.
Consistent artifacts and byte hashes do not establish authenticity, a trusted
collection time, or causation. Runbook coverage remains delta-only: unchanged
non-passing checks are displayed but do not gain invented runbook matches.

## Compatibility and demonstration acceptance

The existing v1alpha1 implementation, default CLI behavior, exact JSON/text
goldens, and replay semantics remain supported. v1alpha2 is an artifact version,
not a product-v2 release. No dependency, workflow permission, live access, model,
release, or mutation capability is added.

Acceptance exercises unchanged FAIL and UNKNOWN, partial and complete recovery,
UNKNOWN-to-PASS/FAIL, additions/removals, omitted optional/mesh evidence,
simultaneous symptoms, Pod/container disagreement, stale deployment generation,
and non-JSON HTTP failure. It also rejects internally valid but mismatched
snapshots/comparisons/mappings and tampered derived fields. Reviewed exact
v1alpha2 goldens and offline CLI replay make four adverse operator situations
visible without reopening the source snapshots to interpret the brief.
A fifth scenario is a positive control for complete recovery of supplied checks.

The five committed synthetic scenarios live in
[`tests/fixtures/forgeops/incident-context`](../../tests/fixtures/forgeops/incident-context).
The dedicated 22-test suite includes independently specified expected states,
exact JSON/text fixtures, collection-to-brief readiness and HTTP regressions,
and fail-closed CLI paths. The existing installed-wheel acceptance also checks
v1alpha2 text, exact JSON, and replay on Python 3.11-3.14. Hosted results are
recorded on the draft PR; this design does not claim live acceptance or a release.
