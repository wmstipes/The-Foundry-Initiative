# Milestone 061 — ForgeOps adversarial evaluation and model-readiness decision

**Status:** Complete, merged, synchronized, and cleaned up through implementation PR #58 and grouped closeout PR #59

**Started:** 2026-09-19

## Goal

Pressure-test the deterministic incident-brief trust boundary and make an
explicit model/retrieval go/no-go decision without adding runtime capability.

## Deliverables

- `forgeops.incident-adversarial-evaluation/v1alpha1`, containing nine sorted
  synthetic boundary cases.
- Offline tests that execute each accepted or rejected behavior through current
  production briefing seams.
- The [model and retrieval readiness decision](../design/forgeops-model-readiness-decision.md).

## Decision

Model and retrieval integration are **deferred**. Deterministic briefing is
ready for a separately approved read-only end-to-end demonstration, but no
measured unmet need, representative model corpus, improvement threshold,
privacy boundary, dependency choice, or failure-mode policy yet justifies a
probabilistic component.

## Evaluated boundaries

- neutral evidence and added passing checks remain `CHANGED`;
- removed or unknown evidence remains `INCOMPLETE`;
- uncertainty takes precedence over failure interpretation;
- mixed recovery and neutral change is not overstated as `RECOVERED`;
- stale windows and fabricated mapping reasons fail before output;
- mapping gaps remain visible with `mapping-incomplete`; and
- structurally valid altered titles demonstrate that validation is not
  authenticity.

## Exit semantics

No new CLI command or exit domain is added. Existing offline tests must pass;
their process exit reports evaluation success, not contained system health.

## Acceptance

- The corpus has exact ordered fields, nine sorted unique cases, and fixed
  dispositions, state expectations, uncertainty, boundaries, and limitations.
- Every case is exercised through current deterministic code.
- Package version and dependencies remain unchanged from Milestone 060.
- The CLI surface is unchanged.
- No model-related module is imported or dependency installed.
- All repository, compilation, manifest, and whitespace checks pass offline.

## Explicit exclusions

No model, prompt, embeddings, retrieval, external service, network access,
live incident input, cluster access, endpoint access, deployment, persistent
state, recommendation, or remediation is added.
