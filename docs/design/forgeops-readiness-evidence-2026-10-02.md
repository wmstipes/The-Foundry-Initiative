# ForgeOps readiness evidence repair — October 2, 2026

## Purpose and reviewed baseline

This change strengthens the incident-copilot demonstration by preventing two
known false-PASS results before evidence reaches the brief. It adds no model,
new resource query, HTTP endpoint, permission, or cluster operation.

Reviewed [PR #169](https://github.com/wmstipes/The-Foundry-Initiative/pull/169) while draft
at `c80f76fc64eca2d1a30d8b68a95daefef5e08202`, including its
[ranked review](https://github.com/wmstipes/The-Foundry-Initiative/blob/c80f76fc64eca2d1a30d8b68a95daefef5e08202/docs/design/forgeops-incident-reasoning-review-2026-10-02.md)
and bounded incident-reasoning design. Its Node/APIService uncertainty repairs,
exact Restaurant endpoint selectors, and delta-only text warning fit its
documented scope. Hosted Required Validation, ForgeOps CI, and Repository
Security Validation passed on that head. The local semantic regression module
also passed. Those checks do not close the remaining evidence gaps.

This follow-up originally started from main
`2ae9f5ebfceb703a7b9a688c6f9074e8b300b108`. On October 3, PR #169 merged
at `0e50669de078d02a75cb9fdbacaa6c0b863805e1`. PR #170 now incorporates
that main commit, preserves both implementations, and reconciles their shared
test inventory. PR #170 remains draft and unmerged. ForgeOps 1.0.0 is already
released; this is source hardening, not a new v1 release or publication.

## Collection and evaluation decision

The existing allowlisted Pod and Deployment responses already contain the
required fields. Normalization now retains Pod `status.conditions` entries of
type `Ready` with only `type` and `status`, Deployment `metadata.generation`,
and Deployment `status.observedGeneration`. Pod condition reasons, messages,
timestamps, and custom condition types are discarded. No additional reads run.

Kubernetes documents that a Pod's Ready condition can be false even when all
containers are ready because a readiness gate is unsatisfied. See
[Pod conditions](https://kubernetes.io/docs/concepts/workloads/pods/pod-condition/).
The [Deployment API](https://kubernetes.io/docs/reference/kubernetes-api/apps/deployment-v1/)
defines observedGeneration as the generation seen by the controller. The
following conservative evaluation policy uses those observations without
claiming a cause or full rollout completion:

| Supplied evidence | Check result |
| --- | --- |
| Exactly one Pod Ready condition, literal string `True`, containers ready, existing phase/image/digest checks satisfied | `PASS`, or existing restart `WARN` |
| Literal Pod Ready `False`, including ready containers | `FAIL` |
| Pod Ready `True` but a container is not ready | `FAIL` |
| Pod Ready `Unknown` | `UNKNOWN`, `condition-unknown` |
| Missing or duplicate Pod Ready condition | `UNKNOWN`, `incomplete-evidence` |
| Malformed Ready value or non-list conditions | `UNKNOWN`, `unexpected-shape` |
| Valid observed generation behind desired generation, even with matching replica counts | `UNKNOWN`, `stale-generation` |
| Observed generation ahead of desired generation | `UNKNOWN`, `inconsistent-generation` |
| Missing/malformed generation or replica count | `UNKNOWN`, `unexpected-shape` |
| Equal valid generations | Continue existing replica and image checks; equality alone does not establish `PASS` |

Desired generation must be a positive integer; observed generation must be a
nonnegative integer. Zero observed generation is stale. Replica counts must be
nonnegative integers. Booleans, floating point numbers, and numeric strings
are rejected rather than coerced. Incomplete readiness takes precedence over
runtime mismatches in the same check, consistent with snapshot UNKNOWN
precedence. A stale status is an evidence gap, not proof of a failed rollout.

## Compatibility and disclosure

The serialized snapshot, comparison, mapping, and brief schemas stay at their
existing v1alpha1 versions. No fields, ordering, check IDs, scope strings,
fixed limitations, or exit-code meanings change. Normalized raw evidence is an
internal collector model, not the serialized snapshot contract.

New snapshots include readiness/generation details in existing expected and
observed strings. Comparing old and new collection output can therefore yield
`EVIDENCE_CHANGED` without a workload change. Newly collected absent, invalid,
or stale evidence can yield snapshot exit 2 where older code falsely passed.

Old saved snapshots and replay goldens still load unchanged. Offline validation
checks their recorded structure and summary; it neither reconstructs discarded
fields nor re-evaluates old PASS results under the stronger collector. Retain
the reviewed source identity alongside demonstration evidence. A valid old
artifact is not proof that these readiness gates were checked.

The raw healthy fixture now explicitly supplies generations and Pod Ready
conditions for all five workloads. Historical evaluated fixtures are unchanged.

## Offline demonstration and validation

Run from this source checkout without a kubeconfig or live runner:

~~~text
python -m unittest tests.test_forgeops_readiness -v
~~~

The 13 functions use synthetic collection, evaluated snapshot serialization,
strict loading, comparison, runbook mapping, and brief serialization/loading.
They cover readiness disagreement, missing/duplicate/malformed conditions,
stale and impossible generations, all five allowlisted workloads, strict
numeric types, current-generation positive controls, and simultaneous Pod FAIL
and Deployment UNKNOWN facts. Before implementation, the initial 11 functions
produced 39 failing subcases and one missing-field error on the baseline.

Acceptance requires the focused pipeline tests, unchanged historical replay,
static documentation checks, and hosted validation on the proposed head.
The local focused pipeline selection passed 122 unittest cases, including all
13 new readiness functions and the existing evidence, comparison, mapping,
brief, and replay suites.
Combining the source and tests with PR #169 in an isolated offline checkout
passed the same selection plus its semantic regressions: 128 unittest cases.
Source changes combined cleanly. The October 3 conflict resolution preserves
both suites and reconciles the documentation inventory to 203 ForgeOps /
289 top-level / 305 complete Python functions.
Original local Windows execution had three pre-existing path/archive test failures in
the wider ForgeOps suite (197 run: 194 pass, three fail): archive path rejection,
normal-install provenance path formatting, and explicit kubectl path formatting.
Complete local discovery also lacks optional test dependencies. These
limitations must remain visible alongside hosted results.
No live cluster evidence was collected and no live resource was changed.

## Remaining admission gate

This closes the two collection false-PASS reproductions from finding 3 of
PR #169. It does not fix aggregate evidence loss in `incident-brief/v1alpha1`.
That state still summarizes deltas: unchanged failures can be STABLE, partial
recovery can be RECOVERED, and UNKNOWN-to-PASS does not prove recovery from a
known failure. PR #169's text warning remains necessary.

The next contract decision must explicitly version aggregate and coverage
semantics, preserve old v1alpha1 replay, and distinguish unchanged failure,
partial recovery, regained evidence, and omitted evidence. Acceptance must
include these readiness cases, simultaneous symptoms, non-JSON HTTP errors,
and absent mesh/path evidence. Collection repairs do not establish mesh
reachability, artifact authenticity, current health, or causal diagnosis.
