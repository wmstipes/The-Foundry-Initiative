# Milestone 058 — ForgeOps deterministic structured incident brief

**Status:** Complete, merged, synchronized, and cleaned up through implementation PR #55 and grouped closeout PR #59

**Started:** 2026-09-19

## Goal

Create a deterministic, machine-readable incident brief from one explicit
validated comparison and one explicit validated runbook mapping without adding
diagnosis, model inference, network access, or operational authority.

## Delivered interface

~~~text
forgeops incident brief \
  --comparison <comparison.json> \
  --mapping <mapping.json> \
  --format json
~~~

Successful rendering returns process exit `0` for every bounded state. Invalid,
unreadable, or cross-document-inconsistent inputs return `2`; process exit `1`
is unused. The exit therefore reports briefing success, not contained health.

## State model

| State | Supplied-window meaning |
| --- | --- |
| `STABLE` | No deltas exist. |
| `INCOMPLETE` | At least one delta ends `UNKNOWN` or removes a check. |
| `DEGRADED` | Otherwise, at least one delta ends `WARN` or `FAIL`. |
| `RECOVERED` | Otherwise, every delta moves from non-passing to `PASS`. |
| `CHANGED` | Valid deltas exist but none of the preceding rules applies. |

`CHANGED` makes the Milestone 056 vocabulary total without forcing a neutral
change into a false health interpretation. Every label describes only the
supplied comparison window.

## Cross-document and output boundary

The brief requires identical comparison windows and delta counts. Every mapping
reason must match an exact comparison identifier, delta kind, and after status;
unmapped identifiers must equal the remaining comparison deltas.

`forgeops.incident-brief/v1alpha1` contains only source schemas, window
timestamps, bounded state, cited delta identifiers/kinds/statuses, cited
runbooks and mapping reasons, unmapped identifiers, enumerated uncertainty, and
fixed limitations. It excludes raw evidence, Kubernetes objects, endpoint
bodies, addresses, credentials, diagnosis, recommendations, and remediation.

## Acceptance

- The five existing synthetic cases produce their expected accepted states.
- Neutral evidence changes produce `CHANGED`.
- `INCOMPLETE` takes precedence over degraded interpretation.
- JSON is deterministic and disclosure bounded.
- Cross-document mismatches fail with exit `2` and no partial output.
- Tests construct no collection or network runner.
- Package metadata advances locally to `0.13.0`; no package is published.

## Explicit exclusions

No text narrative, expected-brief replay, model, retrieval, live incident
claim, cluster access, endpoint access, deployment, or mutation is added.
