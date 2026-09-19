# Milestone 057 — ForgeOps runbook-mapping validation

**Status:** Implementation complete; publication pending

**Started:** 2026-09-19

## Goal

Strictly validate one explicitly supplied saved
`forgeops.runbook-mapping/v1alpha1` artifact before it can become an input to
bounded incident briefing.

## Delivered interface

~~~text
forgeops runbook mapping validate --input <mapping.json>
~~~

The command returns validation exit `0` for a contract-valid mapping, including
a valid mapping whose contained `mappingExit` is `1`. Unreadable or invalid
input returns `2`; validation exit `1` is unused.

## Validation boundary

The loader enforces a 256 KiB limit, UTF-8 JSON, duplicate-key rejection, exact
ordered fields, supported schemas and enumerations, UTC-second timestamps,
chronology, safe repository-relative runbook paths, sorted unique identifiers,
internally consistent mapped and unmapped delta sets, recalculated counts and
mapping exit, and exact limitation text.

Validation proves only that the supplied mapping satisfies its serialized
contract. It does not prove that the mapping was produced from the canonical
catalog, that a referenced procedure applies, or that the artifact is
authentic. It establishes no health, severity, cause, diagnosis,
recommendation, or remediation authority.

## Acceptance

- Current deterministic mapping output round-trips through the strict loader.
- Both complete and incomplete valid mappings return validation exit `0`.
- Invalid or unreadable input returns `2` without partial output or path
  disclosure.
- Oversized, duplicate-key, unsafe-path, unordered, and inconsistent documents
  fail closed.
- Tests construct no collector, Kubernetes runner, or HTTP runner.
- Package metadata advances locally to `0.12.0`; no package is published.

## Explicit exclusions

No incident state, brief generation, replay, diagnosis, model, retrieval,
network access, cluster access, endpoint access, deployment, or mutation is
added.
