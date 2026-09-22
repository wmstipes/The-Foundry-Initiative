# Console C6 — plugin compatibility and distribution planning

## Status and purpose

Planning started after C5 boundary-design PR #106 merged at `c8abc6d` and the
operator confirmed laptop sync. The operator asked to move forward and raised
multi-context/EKS usability. This is a planning proposal, not acceptance of
all C6 implementation gates or authority to access a cloud cluster.

C6 should prove that the existing built-in plugins can evolve predictably and
prepare a future release. The recommended distribution decision is to retain
compiled first-party plugins for the next release candidate. No concrete need
for independently installed third-party modules has yet been established.

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
