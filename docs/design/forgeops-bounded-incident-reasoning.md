# ForgeOps bounded incident reasoning design

## Status

Accepted Milestone 056 design and synthetic evaluation boundary. No production
incident command or model integration exists.

## Purpose

A future ForgeOps incident brief may assemble validated comparison facts and
deterministic runbook mappings into a concise operator-facing explanation. Its
job is to preserve evidence traceability and uncertainty, not to turn a small
point-in-time snapshot into an authoritative diagnosis.

## Proposed explicit interface

~~~text
forgeops incident brief \
  --comparison <forgeops.comparison/v1alpha1 file> \
  --mapping <forgeops.runbook-mapping/v1alpha1 file> \
  --format text|json
~~~

This interface is a design target only. A later milestone must add a strict
mapping-result loader before implementing the command.

## Proposed deterministic state vocabulary

| State | Bounded meaning |
| --- | --- |
| `STABLE` | The supplied comparison contains no deltas. |
| `DEGRADED` | At least one supplied delta ends in `WARN` or `FAIL`. |
| `INCOMPLETE` | At least one supplied delta ends in `UNKNOWN`; uncertainty takes precedence. |
| `RECOVERED` | Changed checks end in `PASS` after an earlier non-passing state, with no later non-passing delta. |

These labels summarize the supplied artifacts only. They are not incident
severity, current health, business impact, or causal analysis.

## Proposed brief contract

`forgeops.incident-brief/v1alpha1` should contain only:

- comparison timestamps and bounded state;
- cited delta identifiers, kinds, and before/after statuses;
- cited runbook IDs, repository paths, sections, and mapping reasons;
- explicit unmapped deltas;
- explicit uncertainty statements;
- source contract versions; and
- fixed authority limitations.

It should omit raw evidence observations, Kubernetes objects, HTTP bodies,
credentials, addresses, kubeconfig paths, and invented causal narratives.

## Required reasoning rules

1. Every factual statement must trace to a validated comparison field or a
   validated mapping field.
2. No cause may be asserted because current inputs contain correlation and
   state transition data, not causal evidence.
3. `UNKNOWN` must be described as incomplete evidence, never converted into a
   failure or a healthy result.
4. A runbook match must be described as a catalog rule match, not as proof that
   the procedure applies.
5. Unmapped deltas must remain visible.
6. Stable, degraded, incomplete, and recovered describe the supplied time
   window only; none establishes current health.
7. The brief may point an operator to reviewed material but may not instruct
   ForgeOps to execute it or mutate the cluster.

## Evaluation corpus

`tests/fixtures/forgeops/incident-reasoning-evaluation.json` covers the five
existing synthetic scenarios. Each case binds the future brief to current
comparison and mapping behavior and records:

- the expected bounded state;
- comparison and mapping exits;
- exact delta and runbook identifiers;
- required uncertainty statements; and
- claims that must remain forbidden.

Tests recalculate the comparison and mapping expectations from the existing
strict loaders and deterministic mapping seam. The corpus is synthetic
evaluation data, not captured SignalForge evidence or model-training data.

## Model boundary

No language model is justified until a deterministic brief implementation can
pass this corpus. If a later milestone evaluates a model, it must receive only
validated, disclosure-bounded inputs; citations and forbidden-claim checks must
remain deterministic; model output must be treated as untrusted draft text;
and no network, kubeconfig, credential, or mutation authority may be inherited.

## Deferred implementation prerequisites

- Strictly load `forgeops.runbook-mapping/v1alpha1`.
- Define and strictly validate `forgeops.incident-brief/v1alpha1`.
- Implement deterministic briefing before considering model-assisted wording.
- Add exact expected brief artifacts and offline replay.
- Separately review any retrieval or model dependency, privacy boundary,
  evaluation threshold, failure mode, and operator disclosure.
