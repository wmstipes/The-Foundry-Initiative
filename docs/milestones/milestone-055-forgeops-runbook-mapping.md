# Milestone 055 — ForgeOps deterministic grounded runbook mapping

**Status:** Implementation complete and merged; documentation-only closeout in progress

**Started:** 2026-09-19

**Implementation branch:** `codex/milestone-055-forgeops-runbook-mapping`

**Baseline:** clean `main` at `a4fbf0d9d1d71e81d7bbf2f290559b7e9e45d6e9`

## Goal

Map one explicitly selected, strictly validated comparison document to one
explicitly selected, strictly validated runbook catalog. Every match must cite
the exact comparison delta and cataloged repository section that caused it.

Mapping reports deterministic rule matches. It does not prove that a procedure
is operationally applicable, infer a cause, diagnose an incident, recommend an
action, or authorize remediation.

## Interface

~~~powershell
forgeops runbook map `
  --comparison .\comparison.json `
  --catalog .\docs\reference\forgeops-runbook-catalog.json `
  --format text
~~~

`--format json` renders the stable
`forgeops.runbook-mapping/v1alpha1` contract.

## Deterministic mapping

For each immutable comparison delta, ForgeOps evaluates only cataloged:

- exact or prefix check-identifier match;
- delta kind; and
- after status.

Matches retain the runbook ID, title, repository-relative path, exact section,
and the matching check ID, delta kind, and after status. A comparison delta may
support more than one catalog entry, but it is counted once as mapped. Deltas
with no matching rule are reported explicitly and never silently discarded.

## Exit semantics

| Exit | Meaning |
| ---: | --- |
| `0` | Every comparison delta was mapped, including an equivalent comparison with no deltas. |
| `1` | Inputs were valid, but one or more deltas had no catalog match. |
| `2` | The comparison, catalog, or invocation was invalid. |

Mapping exit is independent of contained evidence health and comparison exit.
A known regression or recovery can map completely and return mapping exit `0`.

## Disclosure and authority boundary

- Output includes only timestamps, bounded counts, runbook references, matched
  delta identifiers/kinds/after-statuses, unmapped identifiers, and the fixed
  limitation statement.
- It omits evidence observations, expected and observed values, sources,
  errors, artifact paths, and complete input documents.
- It invokes no collector, kubeconfig, kubectl runner, HTTP runner, network,
  directory discovery, persistence, retrieval service, model, or mutation.
- It does not rank matches, score severity, infer causation, diagnose,
  recommend, execute procedures, or remediate.

## Acceptance

- Pod restart, routing regression, incomplete Metrics API evidence, and routing
  recovery scenarios map to their intended catalog entries.
- The stable scenario is complete with zero deltas and zero matches.
- A removed check without an after status remains explicitly unmapped.
- Text and JSON rendering are deterministic and semantically equivalent.
- Both explicit inputs are fully validated before any output is rendered.
- Invalid-input errors omit operator-supplied paths.
- The complete repository suite, isolated installation, source execution,
  compilation, manifest validation, and whitespace validation pass offline.

## Explicit exclusions

- No mapping-result loader, batch mapping, discovery, history, or retention.
- No incident brief, causal reasoning, severity score, diagnosis,
  recommendation, retrieval, language model, remediation, or mutation.
- No package/image publication, release tag, deployment, live acceptance,
  cluster access, endpoint access, persistent-state change, or Wiki mutation.

## Gates

1. Scope and design — pre-approved and complete.
2. Local implementation and offline acceptance — pre-approved and complete.
3. Publication and pull request — complete; PR #49 published the exact accepted tree.
4. Package/image release — closed as not applicable.
5. Deployment — closed as not applicable.
6. Live acceptance — closed as not applicable.
7. Ready for review — complete after ForgeOps CI run `35413595246` passed.
8. Merge — complete; PR #49 merged at `113e629ee105dce3f3a09d0f12c6bce4f53129a4`.
9. Documentation-only closeout — pre-approved and in progress.
10. Branch cleanup — pre-approved; pending closeout merge verification.

## Publication and merge evidence

- Accepted local implementation commit:
  `bc84d6f3f82098e5026c04bbe10b3bfaa9031e12`.
- Published remote implementation commit:
  `688ec8ea89219ffe40b498ab9fb0fb4105525288`.
- Both commits resolve to exact accepted tree:
  `bf74bd8d8d40ac32c58b04f3b7d43edc19deef9f`.
- ForgeOps CI run `35413595246` completed successfully.
- PR #49 merged at `113e629ee105dce3f3a09d0f12c6bce4f53129a4`;
  the merge resolves to the exact accepted implementation tree.
