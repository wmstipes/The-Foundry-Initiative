# Console C6 — plugin compatibility and distribution planning

## Status and purpose

Planning started after C5 boundary-design PR #106 merged at `c8abc6d` and the
operator confirmed laptop sync. The operator asked to move forward and raised
multi-context/EKS usability. The original proposal is retained below; the
implementation and bounded closeout are recorded here. This does not authorize
cloud cluster access or a public release.

C6 should prove that the existing built-in plugins can evolve predictably and
prepare a future release. The recommended distribution decision is to retain
compiled first-party plugins for the next release candidate. No concrete need
for independently installed third-party modules has yet been established.

## Assessment and review candidate — 2026-09-22

After reviewing the handoff and focused architecture assessment, the operator
asked to move forward. The resulting bounded implementation addresses five
findings: incomplete relationships presented without warnings, stale browser
selections, misleading panic outcomes, unjoined shutdown, and unchecked
browser/core pairing. The initial evidence was local implementation and offline verification;
it does not treat PR #107's merge as authority for cloud/cluster access or a
public release.

The [C6 compatibility/lifecycle record](../design/forgeops-console-c6-compatibility-lifecycle.md)
inventories actual plugins, source pairing, version policy, failure limits,
upgrade/rollback procedure and explicitly deferred work.

| Gate | Current evidence / remaining acceptance |
| --- | --- |
| 1 — Scope | Built-in-only decision retained in implementation; operator accepted the concrete candidate through merged PR #108. |
| 2 — Compatibility | Actual supported set inventoried; missing declared handlers and unsupported browser contributions rejected; exact source pairing implemented. |
| 3 — Lifecycle | Targeted stale-state, panic, cancellation and shutdown fixes implemented with offline tests; no process isolation claimed. |
| 4 — Packaging decision | Matched source identity and whole-pair upgrade/rollback procedure defined; no public distribution. |
| 5 — Verification | Go race tests, browser tests/build, locked module graph, both executable builds and synthetic matched/mismatched/restored-pair rehearsal pass locally; the Windows demo smoke check also passed, but resources tests were blocked before execution. Live and historical-release acceptance remain unperformed. |
| 6 — Review | Documentation and test inventory reconciled; PR #108 merged at `66bf21c39fb5fba08241bd4af741f7fb333a885a`; PR checks passed, operator confirmed green workflows and laptop sync, and approved closeout with the Windows test limitation. |

The [testing guide](../testing-and-validation.md#console-c6-local-validation)
records 54 Go test functions and 19 Vitest cases, separately from 248 existing
top-level Python cases. No new tests merely assert planning prose.

## Bounded closeout — 2026-09-22

[PR #108](https://github.com/wmstipes/The-Foundry-Initiative/pull/108) merged
at `66bf21c39fb5fba08241bd4af741f7fb333a885a`. Required Validation and
Repository Security Validation passed on the PR. The operator reported green
workflows after merge and supplied the matching laptop HEAD.

Windows evidence is operator-provided terminal output and smoke-check results:

- All 19 Vitest cases and the production frontend build passed.
- The production Go executable build returned exit code 0; the operator also
  successfully built and launched the separate synthetic demo.
- Other Go packages passed, some from cache. `internal/resources` did not run:
  Windows Application Control blocked the generated `resources.test.exe`
  before execution (Code Integrity event 3077). Smart App Control was On;
  the specific policy was not resolved from a policy-loading event.
- The operator confirmed the synthetic banner, context activation, namespace
  selection, Pod-to-Service transition clearing old rows and selection, and
  prompt return after Ctrl+C, with no errors.

The operator approved moving forward with this limitation recorded. C6's
compiled-first-party scope and implementation review are closed; full Windows
Go test validation remains incomplete. Successful compilation and the demo
smoke check do not replace the blocked resources tests. No security settings
were changed as part of this acceptance workflow.

Before claiming full Windows support, resolve the application-control conflict
through an approved development/signing setup and execute the blocked resources
suite. No additional tests are justified by this OS launch block. Windows
mismatched-bundle rejection, historical-release rollback, production startup
with kubeconfig, and live-cluster behavior were not verified by this smoke check.
C7 must define release acceptance independently; this closeout does not publish
a release or complete C5 export and aligned operator acceptance.

## Baseline to evaluate

The example, resource-browser, and diagnostics plugins are compiled with the
Go core. The current SDK version is `0.1.0`. Manifest validation accepts the
literal compatibility string `>=0.1.0 <0.2.0`; it does not implement general
semantic-version range negotiation. The browser also contains built-in views.
This is an internal contract, not evidence of a stable external SDK or runtime
extension API.

Evaluate registry validation, capability dispatch, browser contribution
handling, errors, cancellation, and scope generations using actual modules.
Document that in-process modules do not have process or security isolation;
capability checks do not sandbox arbitrary Go code. Any failure-containment
claim must distinguish returned errors, panics, blocked handlers, and process
failure.

## Proposed deliverables and gates

| Gate | Work and exit evidence |
| --- | --- |
| 1 — Scope | Review built-in-only recommendation, supported plugin set, and explicit exclusions. |
| 2 — Compatibility | Inventory real manifests/capabilities/contributions; define version policy, supported pairings, and incompatible-manifest behavior. Identify concrete gaps before adding tests. |
| 3 — Lifecycle | Review startup/registration, dispatch, cancellation, teardown, UI/core mismatch, and failure containment. Define bounds without claiming process isolation. |
| 4 — Packaging decision | Specify a matched core/browser/plugin bundle and how build identity is checked; define upgrade/rollback procedure and configuration expectations. Defer actual public binaries and release publication to C7. |
| 5 — Verification | Exercise meaningful compatibility and lifecycle failures offline, verify existing modules still function, and rehearse candidate upgrade/rollback with synthetic configuration if implementation is admitted. |
| 6 — Review | Reconcile scope, evidence, remaining limitations, and test counts; publish a review PR, verify checks, then operator merge and laptop sync. |

Do not add tests merely asserting documentation prose. Preserve existing
read-only cluster authority, explicit file selection, credential separation,
bounded diagnostics, and C5's distinction between proposed artifacts and
implemented evidence intake. No marketplace, dynamic loader, signing service,
release, or live cluster access is part of this proposal.

## Context selection and EKS follow-up

The loader lists all contexts from one explicit file at startup. Selecting a
context and activating it changes the session; namespace selection is then
explicit. File additions require core restart. It does not follow ambient
`kubectl config use-context` changes or edit kubeconfig state.

EKS is a real usability requirement to investigate, but authentication adapters
belong in the credential-owning core rather than ordinary UI plugins. Standard
EKS authentication invokes `aws eks get-token`, whereas the current live factory
rejects `Exec` and `AuthProvider` configuration. Adding an EKS context alone
does not make it usable. This is verified against source and
[AWS documentation](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html).

Before cloud authentication implementation, compare a core-owned AWS adapter
with narrowly constrained executable credential support. Specify explicit
profile/account/role/region selection, SSO/MFA interaction, token expiry and
refresh, trusted executable resolution if applicable, subprocess arguments and
environment, time/output limits, cancellation, credential redaction, endpoint
reachability, and synthetic denial/expiry tests. General kubeconfig-provided
command execution is not an acceptable default.

C6 should record the decision boundary and assess unsupported-auth messaging.
It does not silently relax exec restrictions or authorize AWS API calls,
credential discovery, cloud resources, or chargeable infrastructure. Cloud auth
implementation requires its own reviewed scope. No temporary-token copying
workaround is proposed.

## Separate work

C5 export/validator implementation and aligned operator acceptance remain
follow-ups. Istio installation/mesh inspection and ForgeFire are separate
proposals. C7 will decide supported environments, release identity, installed
artifact acceptance, provenance, and public distribution.
