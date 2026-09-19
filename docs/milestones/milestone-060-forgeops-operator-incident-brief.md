# Milestone 060 — ForgeOps deterministic operator incident brief

**Status:** Implementation complete; publication pending

**Started:** 2026-09-19

## Goal

Render the accepted structured incident brief as concise deterministic text for
human review without adding facts, inference, recommendations, or authority.

## Delivered interface

~~~text
forgeops incident brief \
  --comparison <comparison.json> \
  --mapping <mapping.json> \
  --format text|json
~~~

Text becomes the default operator view; JSON remains explicit and unchanged.
Both formats derive from the same immutable brief model and share process exit
`0` for successful rendering and `2` for invalid or inconsistent inputs.

## Text boundary

The fixed sections are supplied window and bounded state, deterministic facts,
cataloged runbook references, unmapped deltas, uncertainty, and authority
limitations. Runbooks are labeled informational and their reasons are rendered
as matched catalog rules. The renderer does not add likely cause, severity,
impact, recommended action, or execution language.

## Acceptance

- Every synthetic case has an exact golden text brief.
- Repeated rendering is byte-identical.
- Text and JSON expose the same states, fact identifiers, and runbook IDs.
- Stable output still shows point-in-time uncertainty and authority limits.
- Incomplete output preserves evidence uncertainty.
- Output contains no raw observations, private input paths, or new evidence.
- Tests remain offline and construct no collection or network runner.
- Package metadata advances locally to `0.15.0`; no package is published.

## Explicit exclusions

No generated prose, model, retrieval, prioritization, diagnosis,
recommendation, live input, cluster access, endpoint access, deployment, or
mutation is added.
