# Milestone 062 — ForgeOps deterministic incident-copilot demonstration

**Status:** Complete and merged through PR #63; documentation-only closeout
in progress

**Started:** 2026-09-19

## Governing purpose

This milestone directly improves the final incident-copilot demonstration and
proves that it is trustworthy. It does not add capability merely to continue
the milestone sequence.

## Goal

Demonstrate the existing deterministic ForgeOps path from bounded evidence to
an operator-facing incident brief while keeping live observations, synthetic
evaluation, exit domains, uncertainty, and operational authority visibly
separate.

## Approved demonstration design

The [demonstration guide](../guides/forgeops-incident-copilot-demonstration.md)
defines two tracks:

1. an offline synthetic routing regression that exercises strict validation,
   comparison, grounded runbook mapping, mapping validation, JSON and text
   briefing, and exact expected-brief replay; and
2. a separately executed live read-only baseline using two explicitly
   authorized bounded snapshots without injecting a failure.

A naturally stable live window is an accepted truthful outcome. The synthetic
track demonstrates degraded-state behavior without misrepresenting a fixture
as a live incident.

## Offline rehearsal evidence

The initial source-launcher rehearsal at the accepted starting commit
`53a9a57783f0f3afa3fc7c362684b14011f5c25f` produced:

- consistent source execution provenance for repository-local version
  `0.15.0`;
- contract-valid `before` and `after` routing-regression evidence;
- a contract-valid runbook catalog with seven entries and fourteen signals;
- comparison exit `1`, correctly meaning valid artifacts differed;
- one mapped delta, no unmapped deltas, and mapping exit `0`;
- a deterministic `DEGRADED` operator brief citing only
  `routing.forge-restaurant.synthetic-service` and the cataloged
  `service-endpoints` runbook section; and
- incident replay exit `0`, correctly meaning exact expectation equality.

No kubeconfig, kubectl, HTTP runner, cluster, endpoint, model, retrieval
service, or external service was used during this rehearsal. Temporary output
was removed after review.

## Live read-only acceptance evidence

The approved operator-workstation demonstration used the exact published source
at `8dd94800e2e13b71b1984aaef7ac71bd632b6e7d`, one explicit kubeconfig, the
exact `kubernetes-admin@kubernetes` context, and the two documented private-lab
application URLs.

- Source provenance was consistent for repository-local version `0.15.0`.
- The supplied window was `2026-09-19T18:08:08Z` through
  `2026-09-19T18:09:32Z`.
- Both bounded snapshots contained 33 checks, overall `PASS`, and snapshot exit
  `0`.
- Both saved artifacts strictly validated, and immediate integrity verification
  reported matching length, digest, and metadata. This demonstrates only a
  match to the colocated records at verification time, not authenticity or
  chain of custody.
- Deterministic comparison returned exit `0` with zero changed checks.
- The runbook mapping strictly validated with zero deltas, zero mapped or
  unmapped deltas, zero runbook matches, and mapping exit `0`.
- JSON and text incident briefs both returned exit `0` and the bounded state
  `STABLE`, with no facts, runbook matches, or unmapped deltas and with
  `point-in-time-only` uncertainty.
- The operator reported no concrete question left unanswered by the
  deterministic brief in this demonstration.

No outage, restart, rollout, configuration change, remediation, write request,
or cluster mutation was used to manufacture the result. The temporary evidence
artifacts remain local and are not repository evidence.

## Acceptance boundary

Milestone acceptance requires:

- exact execution provenance;
- successful offline regression rehearsal through existing production seams;
- two valid bounded live snapshots collected only after explicit approval;
- integrity creation and immediate verification described without an
  authenticity or chain-of-custody claim;
- a valid deterministic comparison and runbook mapping;
- equivalent structured and operator-facing incident briefs;
- visible uncertainty, unmapped deltas, and authority limitations; and
- a recorded answer about whether the deterministic brief left a concrete
  operator question unmet.

## Explicit exclusions

No ForgeOps code, CLI, schema, version, dependency, package, image, manifest,
deployment, failure injection, model, retrieval engine, external service,
expanded collection, recommendation authority, remediation authority,
persistent state, or cluster mutation is added.

Generated live evidence remains local and untracked. Only reviewed,
disclosure-minimized acceptance facts may be recorded in repository
documentation.

## Approval gates

1. Planning approval — complete; Mike approved the milestone and all ten gates.
2. Documentation reconciliation and offline rehearsal — complete; all 141
   focused ForgeOps tests and all 204 repository Python tests passed, as did
   manifest, Wiki, alert-rule source, compilation, and whitespace validation.
3. Draft-PR publication and CI — complete; draft PR #63 opened from remote
   commit `5c8d26d31037286a9c95bdbb43f824d029bec522`, whose tree
   `46ef3424648abc04a3ea91be9cd7007fcbf1ec57` exactly matched the reviewed
   local tree. GitHub triggered no workflow because the change is outside the
   existing code and manifest path filters; the approved local validation is
   the executable evidence for this documentation-only change.
4. Package or image release — complete as not applicable; no release artifact
   exists and repository-local version `0.15.0` is unchanged.
5. Deployment — complete as not applicable; no image, manifest, workload,
   configuration, rollout, restart, or persistent state changes.
6. Live read-only demonstration — complete; both snapshots, integrity checks,
   comparison, mapping, and briefs passed within the approved boundary.
7. Acceptance review and PR readiness — complete; accepted remote head
   `b7969d888f9ca032c9a7969af3783d154e565ae2` resolved to tree
   `18894b421b35d9c2d959946f15448396140fe454`, exactly matching the accepted
   implementation tree, and PR #63 was marked ready.
8. Merge — complete; PR #63 was squash-merged at
   `6e7e5802037fa55245761410196f165281a4c804`.
9. Documentation-only closeout — in progress through PR #64; this update
   records the accepted demonstration and merge without adding operational
   capability.
10. Branch cleanup and synchronization — pending.

## Merge and publication evidence

- Accepted implementation head: `b7969d888f9ca032c9a7969af3783d154e565ae2`.
- Exact accepted implementation tree: `18894b421b35d9c2d959946f15448396140fe454`.
- Implementation PR: #63.
- Squash merge: `6e7e5802037fa55245761410196f165281a4c804`.
- Documentation-only closeout PR: #64.
- GitHub Actions did not run because the documentation-only paths were outside
  the repository's workflow filters; the approved local suites and validators
  remain the executable acceptance evidence.

## Deferred decisions

Model and retrieval integration remain deferred because the demonstration
identified no concrete unmet operator question. A one-command orchestrator,
broader telemetry, and remediation also remain deferred unless later evidence
identifies a need that satisfies the governing milestone rule and is approved
separately.
