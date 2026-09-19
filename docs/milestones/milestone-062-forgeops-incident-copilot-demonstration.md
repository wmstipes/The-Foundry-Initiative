# Milestone 062 — ForgeOps deterministic incident-copilot demonstration

**Status:** In progress; plan approved and offline rehearsal passed, live
read-only acceptance pending

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
3. Draft-PR publication and CI — pending.
4. Package or image release — approved as not applicable unless scope changes.
5. Deployment — approved as not applicable unless scope changes.
6. Live read-only demonstration — approved; execution remains pending because
   it requires the operator workstation's explicit kubeconfig and private-lab
   reachability.
7. Acceptance review and PR readiness — pending.
8. Merge — pending.
9. Documentation-only closeout — pending.
10. Branch cleanup and synchronization — pending.

## Deferred decisions

Model and retrieval integration remain deferred. A one-command orchestrator,
broader telemetry, and remediation remain deferred unless this demonstration
identifies a concrete need that satisfies the governing milestone rule and is
approved separately.
