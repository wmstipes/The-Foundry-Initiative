# ForgeOps model and retrieval readiness decision

## Decision

**DEFER model and retrieval integration.**

The deterministic briefing workflow is ready for a separately approved
read-only end-to-end demonstration. The current evidence does not justify
adding a language model, embedding model, retrieval service, vector database,
external API, or model SDK.

## Why

- Deterministic briefing now covers the accepted five-case synthetic corpus
  with exact JSON and text expectations.
- Nine additional adversarial cases exercise neutral changes, missing evidence,
  mixed states, stale mappings, fabricated reasons, mapping gaps, and the
  distinction between structural validity and authenticity.
- No measured operator task currently requires probabilistic wording beyond
  the deterministic facts, catalog-rule matches, and uncertainty already shown.
- Five expected scenarios and nine boundary cases are sufficient to test the
  current contract, but not to establish a representative model-quality
  benchmark.
- A model cannot repair the remaining provenance limitation: a structurally
  valid altered runbook title is still unauthenticated input.
- No approved privacy boundary, dependency choice, quality threshold, or
  failure-mode policy exists for model output.

## What is accepted now

- Strict mapping and brief loading.
- Cross-document consistency checks.
- Total deterministic state classification.
- Exact JSON and text briefs.
- Exact offline replay.
- Visible uncertainty and unmapped deltas.
- Informational runbook references without execution authority.

This acceptance is limited to explicitly supplied offline artifacts. It does
not establish current SignalForge health or authorize live access.

## Conditions to reconsider

Model or retrieval work may be proposed only after an approved read-only
end-to-end demonstration identifies a concrete operator question that the
deterministic brief cannot answer. A later proposal must define:

1. a representative evaluation corpus independent of model training;
2. a measurable improvement threshold over the deterministic baseline;
3. deterministic citation and forbidden-claim enforcement;
4. privacy, retention, and local-versus-remote processing boundaries;
5. dependency, availability, timeout, and failure behavior;
6. treatment of all model output as untrusted draft text; and
7. continued absence of kubeconfig, credential, endpoint, or mutation authority.

## Authority boundary

This decision adds no runtime command, model, retrieval engine, dependency,
network access, cluster access, endpoint access, deployment, persistent state,
recommendation, or remediation capability.
