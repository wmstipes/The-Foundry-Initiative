# Milestone 059 — ForgeOps incident-brief replay and evaluation

**Status:** Complete, merged, synchronized, and cleaned up through implementation PR #56 and grouped closeout PR #59

**Started:** 2026-09-19

## Goal

Strictly load deterministic incident briefs and replay one actual brief against
one explicit expected brief without adding collection, diagnosis, or model
reasoning.

## Delivered interface

~~~text
forgeops incident replay \
  --comparison <comparison.json> \
  --mapping <mapping.json> \
  --expected <incident-brief.json>
~~~

Replay exit `0` means exact equality, `1` means valid inputs produced a
mismatch, and `2` means an input is unreadable, invalid, or inconsistent. A
`DEGRADED` or `INCOMPLETE` expected brief can therefore replay successfully
with exit `0`.

## Strict expected-brief boundary

The `forgeops.incident-brief/v1alpha1` loader enforces a 256 KiB limit, UTF-8
JSON, duplicate-key rejection, exact fields and order, supported schemas,
states, kinds, and statuses, chronology, safe runbook paths, sorted unique
identifiers, fact/reason/coverage consistency, recalculated state and
uncertainty, and exact limitations.

## Evaluation corpus

Every existing synthetic scenario now contains an exact expected incident
brief. Tests rebuild each brief through the production comparison, mapping, and
briefing seams before comparing it to the independently stored expectation.
The artifacts remain synthetic evaluation data, not captured SignalForge
evidence, training data, current-health claims, or operational guidance.

## Acceptance

- All five expected briefs strictly validate and match production output.
- Exact replay passes for stable, degraded, incomplete, and recovered cases.
- A valid expectation difference returns `1` without disclosing its content.
- Invalid expectations return `2` without partial output or path disclosure.
- Tests construct no collector, Kubernetes runner, or HTTP runner.
- Package metadata advances locally to `0.14.0`; no package is published.

## Explicit exclusions

No text renderer, model, retrieval, live incident input, directory discovery,
cluster access, endpoint access, deployment, or mutation is added.
