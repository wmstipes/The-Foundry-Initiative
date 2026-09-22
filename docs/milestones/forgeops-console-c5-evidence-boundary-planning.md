# ForgeOps Console C5 — evidence boundary plan

## Status and decision

Planning requested by the operator on 2026-09-22 after C4 closeout merged
through PR #104. The plan merged through PR #105 at `da9acdd`. After syncing
the laptop, the operator approved C5's planned work and all six control gates.
That approval permits the bounded work; it does not establish completed gate
acceptance, authorize live access, or admit an export contract without the
required need assessment.

C5 asks: **Does an explicitly selected Console observation help the operator
understand a ForgeOps incident brief enough to justify another evidence
contract?** An accepted decision to retain the existing ForgeOps commands is
a successful outcome. An export feature is not presumed.

## Existing contract

The [accepted demonstration](../guides/forgeops-incident-copilot-demonstration.md)
already provides provenance, snapshot validation, comparison, runbook mapping,
deterministic briefing, and exact replay. Milestone 062 identified no concrete
unmet operator question. Its historical acceptance remains unchanged.

`src/forgeops/evidence.py` accepts evaluated `forgeops.snapshot/v1alpha1`
artifacts with strict fields, disclosure statements, context, timestamps,
checks, and consistent summaries, under a 1 MiB input limit. It rejects
duplicate keys and invalid schema. Console resource projections, activity
records, previews, logs, and Events are not such evaluated snapshots.

C4 provides bounded observations and explicitly warns that log/Event text is
not guaranteed redacted. A session generation distinguishes Console scope
changes; it is not cluster identity, collection authenticity, or a durable
provenance claim. Existing integrity records establish byte agreement only.
ForgeOps v1.0.0 remains immutable and independently usable.

## Proposed operator exercise

Begin offline, using the reviewed
[synthetic corpus](../../tests/fixtures/forgeops/scenarios/README.md) and the
existing source launcher. Record the exact checkout and execution provenance.
Generated artifacts stay in an operator-controlled temporary directory outside
the repository. Record disclosure-minimized conclusions, not raw output dumps.

| Case | Required interpretation |
| --- | --- |
| routing-regression | A synthetic routing check changes PASS to FAIL; this establishes a reported change, not its root cause. |
| incomplete-evidence | UNKNOWN remains missing evidence; the brief must preserve uncertainty. This fixture concerns Metrics API availability, outside current Console resource views. |
| routing-recovery | FAIL to PASS is a contained recovery observation, not proof of durable health or a successful remediation action. |
| stable-baseline | No material difference is a valid outcome; do not manufacture an incident. |

For each case, validate before/after artifacts, compare them, map against the
reviewed runbook catalog, validate that mapping, render the brief, and replay
against the checked-in expectation using the demonstration guide's offline
sequence. Comparison exit 1 means valid differences; replay exit 0 means an
exact expectation match, not healthy infrastructure.

1. **Baseline:** Have the operator identify the changed check, bounded state,
   uncertainty, and informational runbook reference using existing outputs.
   Record any unanswered question and steps needed to answer it.
2. **Console-assisted review:** Examine how existing resource relationships,
   selected-Pod diagnostics, and scope indicators could answer that question.
   Use the synthetic Console demo only as an illustration unless its data is
   demonstrably aligned with the scenario. Do not present independent demo
   fixtures as corroboration of a ForgeOps snapshot.
3. **Gap assessment:** Record whether the answer is visible already, missing
   from current Console authority, or actually needs a portable observation.
   A missing Metrics API view is not permission to broaden collection.
4. **Comparison:** Record correctness, remaining uncertainty, manual steps,
   and operator feedback. Timing may be recorded but is not a benchmark from
   one rehearsal. If aligned Console fixtures are needed, propose their exact
   scope before implementation; do not claim an end-to-end comparison passed.

The worksheet should contain scenario/source identifiers, operator question,
baseline answer and steps, Console contribution and steps, residual uncertainty,
disclosure considerations, and an explicit integration/no-integration decision.
No live exercise is necessary for this planning PR. Any later live exercise
requires its own bounded authorization; prior C4 access is not ongoing access.

## Admission and rejection criteria

Admit an artifact design only if the exercise demonstrates a concrete repeated
operator need, a specific minimal selected observation answers it, and the
benefit cannot be achieved more clearly with existing commands or documentation.
Require an identified consumer and offline validation path before writing an
exporter. A file with no accepted consumer is not an integration.

Reject or defer integration if it duplicates existing snapshots, obscures
missing evidence, depends on unredacted diagnostics, expands collection merely
to populate a schema, or encourages unsupported causal conclusions. In that
case deliver the operator guide and decision record, with no export code.

If admitted, the next reviewed design must specify:

- A distinct versioned observation contract, exact allowlisted fields, numeric
  byte/item/text limits, strict unknown-field/version and duplicate-key handling,
  and deterministic offline validation. Do not label projections as snapshots.
- Explicit operator selection and review, scope and collection-time semantics,
  source/build identity, synthetic/live distinction, and limitations on identity
  and authenticity. Session generation alone is insufficient provenance.
- Missing, denied, stale, empty, truncated, and timed-out outcomes; empty Events
  do not prove no Events occurred. No silent merging across scopes or times.
- Disclosure minimization and field-level redaction rules. Exclude credentials,
  kubeconfig paths, raw objects, raw logs/Event messages, and activity history
  from the initial candidate; adding any requires a new justification/review.
- A documented consumer decision: retain a separate operator aid or propose a
  separately versioned future ForgeOps intake. Existing v1.0.0 validation must
  not be weakened to accept Console data.
- Export location, retention/deletion ownership, review before sharing, and
  failure behavior. Nothing is automatically saved, uploaded, or admitted as
  evidence. No diagnosis or remediation authority is conveyed.

These are design requirements, not an approved schema or implemented feature.

## Proposed six gates

| Gate | Deliverable and exit condition |
| --- | --- |
| 1 — Scope | Approved: the operator accepted the bounded C5 work package and all six gates after syncing PR #105. Exclusions and the no-integration success path remain in force. |
| 2 — Need | Complete the offline operator worksheet and choose no integration or a justified minimal candidate. Do not infer operator feedback from automated tests. |
| 3 — Boundary | Review the no-integration rationale, or the exact contract, consumer, limits, disclosure model, and failure cases. A candidate that expands approved scope returns for approval. |
| 4 — Delivery | Produce the guide/decision record; implement only an admitted, approved candidate with focused boundary tests. No feature implementation is included in this planning PR. |
| 5 — Verification | Replay reviewed fixtures and verify the selected path. For an artifact, test hostile/oversized/malformed/stale/missing inputs and prove existing ForgeOps compatibility. Separate automated evidence from operator acceptance and any separately authorized live evidence. |
| 6 — Closeout | Review published checks and operator findings, reconcile documentation, merge through normal review, and sync the laptop. Record limitations and the integration decision without claiming a release. |

The design review disposition below separates completed work from pending
acceptance; approval alone does not pass a gate. C6 plugin distribution and
C7 release readiness remain separately gated. C3-UX-01 remains an open label
follow-up, not an implicit part of C5.

## ForgeFire — future troubleshooting training proposal

ForgeFire is a proposed companion project for practicing investigation and
repair of deliberately introduced lab faults. Console could supply read-only
inspection while ForgeFire has a separately designed mutation boundary.

Start with manually selected, reversible scenarios in a dedicated disposable
training namespace: for example, an incorrect Service selector, a bad image
reference, or a deliberately failing readiness probe. Each scenario needs an
explicit target allowlist, known baseline, bounded duration, recovery recipe,
and a tested stop/reset path. Verify recovery rather than promising that a
timer always restores the lab. Keep the fault explanation hidden until the
operator requests a hint or debrief; distinguish symptoms from confirmed cause.

Random selection, unattended runs, node/control-plane disruption, networking
infrastructure changes, and destructive storage faults are later decisions.
Before any implementation or live trial, review permissions, conflict handling
for operator repairs, cleanup failures, and evidence of recovery. C5 may use a
synthetic training narrative but does not implement ForgeFire, inject faults,
grant mutation capabilities to Console, or authorize changes to SignalForge.

## Planning validation

This proposal changes documentation only. Local validation on 2026-09-22 passed
all 248 existing top-level tests (`python -m unittest discover -s tests`),
relative-link target checks for the four changed documents, and
`git diff --check`. No tests or suite counts were added. Published CI remains
separate evidence. Proposed C5 exercises and feature acceptance above remain
pending and must not be counted as executed tests.

## C5 offline rehearsal — 2026-09-22

The assistant ran the existing source launcher at merged checkout
`da9acddb64a2535c55b011274669e388315d78cb`. Provenance reported OK, source
execution, and project/module version 1.0.0. Before/after validation, catalog
validation, mapping validation, comparison replay, and incident replay passed
for all four cases. Generated text briefs also matched the checked-in text
expectations exactly. These are rehearsal results, not new automated tests or
operator acceptance. Outputs were written outside the repository.

| Scenario | Comparison exit | Mapping exit | Brief state | Exact comparison/brief replay |
| --- | ---: | ---: | --- | --- |
| routing-regression | 1 | 0 | DEGRADED | Pass |
| incomplete-evidence | 1 | 0 | INCOMPLETE | Pass |
| routing-recovery | 1 | 0 | RECOVERED | Pass |
| stable-baseline | 0 | 0 | STABLE | Pass |

Source review confirms that the Console demo uses context `synthetic-demo`,
namespace `signalforge`, and different resource identities/counts from the
ForgeOps corpus. Its EndpointSlice has one ready and one not-ready endpoint;
the routing-regression after fixture reports two ready and one not-ready.
No fixture alignment or corroboration is claimed. The
[operator worksheet](../guides/forgeops-console-c5-operator-exercise.md)
records the human feedback and explicitly unperformed assessments.

## Boundary review delivery

The operator identified save/share needs for human help, incident history, and
future ForgeOps use, with Pod Events/logs inspected before Service/EndpointSlice
details. The [C5 contract](../design/forgeops-console-observation-contract.md)
defines a strict candidate with 64 KiB structured JSON, 12 selected observations,
aliases, explicit missing/incomplete states, acquisition timestamps, and a
96 KiB human handoff with up to four separately reviewed diagnostic excerpts.
The excerpt path is a proposed addition to the initial exclusion; it is not
implemented or silently included in machine evidence.

Decision: deliver the human-handoff design and reject automatic ForgeOps
integration for the current implementation. Existing ForgeOps v1.0.0 remains
the supported machine evidence path. A separately reviewed follow-up must
implement and validate the candidate before exports exist. The roadmap's C5
design outcome is ready for review; full end-to-end operator acceptance is
not established by the partial discussion and automated rehearsal.

| Gate | Actual disposition |
| --- | --- |
| 1 | Scope approved by operator. |
| 2 | Save/share needs and investigation order recorded; aligned comparative exercise and repeated benefit remain unproven. Sufficient for a design candidate, not exporter admission. |
| 3 | Exact candidate boundary and no-current-intake decision delivered for PR review. |
| 4 | Operator guide, decision record, and contract delivered. No exporter, schema validator, or ForgeOps intake implemented. |
| 5 | Four existing scenarios replayed exactly; 248 existing repository tests, link-target validation, and whitespace checks passed. Candidate implementation acceptance remains unexecuted. |
| 6 | Published review/checks, merge, and laptop sync remain pending. No release or live activity. |

No feature tests were added and suite counts are unchanged. The proposed Istio
lab learning milestone and future mesh inspection remain separate from C5.
