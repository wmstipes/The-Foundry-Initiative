# Milestone 056 — ForgeOps bounded incident-reasoning design and evaluation

**Status:** Complete, merged, synchronized, and cleaned up

**Started:** 2026-09-19

**Implementation branch:** `codex/milestone-056-forgeops-incident-reasoning-design`

**Baseline:** clean `main` at `5e5bcde2f2e8b1b70e413751b3cfbccc1cb16295`

## Goal

Define the contract, grounding rules, uncertainty requirements, forbidden
claims, and synthetic evaluation cases for a future bounded incident brief
before adding a production reasoning command or language model.

## Deliverables

- The [bounded incident-reasoning design](../design/forgeops-bounded-incident-reasoning.md).
- `forgeops.incident-evaluation/v1alpha1`, a five-case synthetic evaluation
  corpus bound to the existing scenario comparison and runbook-mapping seams.
- Offline tests that recalculate each expected delta and runbook mapping rather
  than trusting duplicated fixture claims.

## Designed state vocabulary

| State | Artifact-bounded meaning |
| --- | --- |
| `STABLE` | The supplied comparison contains no deltas. |
| `DEGRADED` | A supplied delta ends in `WARN` or `FAIL`. |
| `INCOMPLETE` | A supplied delta ends in `UNKNOWN`; uncertainty takes precedence. |
| `RECOVERED` | Changed checks end in `PASS` after an earlier non-passing state. |

These states describe only the supplied comparison window. They do not claim
current health, severity, impact, or cause.

## Evaluation boundary

Each case specifies the expected bounded state, comparison and mapping exits,
exact delta and runbook identifiers, required uncertainties, and forbidden
causation, current-health, severity, and remediation-authority claims.

The corpus covers stable, Pod-restart warning, routing regression, incomplete
Metrics API evidence, and routing recovery. It contains synthetic identifiers
only and is neither captured SignalForge evidence nor training data.

## Trust and authority boundary

- No `forgeops incident` command is added.
- No mapping-result loader or incident-brief schema is implemented.
- No prompt, retrieval engine, language model, model SDK, external service,
  or network dependency is added.
- No diagnosis, recommendation, runbook execution, remediation, or cluster
  mutation occurs.
- Tests load only checked-in synthetic files and current deterministic seams.

## Acceptance

- The evaluation document has exact ordered fields, five sorted unique cases,
  bounded size, fixed uncertainty vocabulary, and fixed forbidden claims.
- Its case inventory exactly equals the existing synthetic scenario corpus.
- Every expected delta, comparison exit, runbook ID, and mapping exit is
  recalculated through production loaders and mapping code.
- No live node names, addresses, context, kubeconfig, credentials, or secrets
  appear in the evaluation file.
- The CLI exposes no incident or reasoning command and package dependencies
  remain unchanged.
- All repository tests, compilation, manifest validation, and whitespace
  validation pass offline.

## Explicit exclusions

- No production reasoning, incident brief, mapping loader, renderer, replay,
  retrieval, language model, prompt, diagnosis, or recommendation.
- No package version change, package/image publication, release tag,
  deployment, live acceptance, cluster access, endpoint access,
  persistent-state change, or Wiki mutation.

## Gates

1. Scope and design — pre-approved and complete.
2. Local implementation and offline acceptance — pre-approved and complete.
3. Publication and pull request — complete; PR #51 published the exact accepted tree.
4. Package/image release — closed as not applicable.
5. Deployment — closed as not applicable.
6. Live acceptance — closed as not applicable.
7. Ready for review — complete after ForgeOps CI run `35414081332` passed.
8. Merge — complete; PR #51 merged at `04b686a6b790133914c4f058f00390f8ab43eaa9`.
9. Documentation-only closeout — complete; PR #52 merged at `548b63ef4acfa436ce79ac9554f8ae7c350ff832`.
10. Branch cleanup — complete; both Milestone 056 branches were deleted locally and remotely.

## Publication and merge evidence

- Accepted local implementation commit:
  `e3616400188a7f0f38934de4cb9e58384a098399`.
- Published remote implementation commit:
  `e8bb716bc5594d5cd467451ff5d9db50de42f5ee`.
- Both commits resolve to exact accepted tree:
  `d8d2073408f2efc64491e294b3604cd11a2a6951`.
- ForgeOps CI run `35414081332` completed successfully.
- PR #51 merged at `04b686a6b790133914c4f058f00390f8ab43eaa9`;
  the merge resolves to the exact accepted implementation tree.
