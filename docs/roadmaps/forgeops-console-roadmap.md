# ForgeOps Console roadmap

**Status:** C1, C2, and C3 accepted; C4 requires separate approval

**Baseline:** ForgeOps v1.0.0; C1 was admitted from repository commit
`8008f6934a0c1bd34a63d6a86a9ad74d170a7671` and merged at
`d363b21d4338849f7063cabeb46fbf1ecc6b65ab`

## Purpose

ForgeOps Console is a proposed local, plugin-ready Kubernetes operations
interface that makes cluster scope, read operations, equivalent commands, and
eventual evidence selection visible to an operator. It directly improves the
incident-copilot demonstration only when it shortens or clarifies the path from
cluster inspection to reviewed deterministic evidence.

It must not become an excuse for broad cluster authority, autonomous
remediation, ambient credentials, background collection, or an unbounded
dashboard platform.

## Governing outcomes

Every Console work package must do at least one of the following:

1. improve the operator's incident-copilot demonstration workflow;
2. prove the Console and evidence boundary are trustworthy; or
3. prepare a deliberate independently versioned Console release.

Feature count, framework exposure, and similarity to another Kubernetes UI are
not success measures.

## Preserved boundaries

- ForgeOps v1.0.0 remains immutable and independently usable without Console.
- One explicit kubeconfig path and one explicit selected context are required;
  ambient and in-cluster credentials are rejected.
- The browser never receives kubeconfig content or credentials.
- The initial core uses typed Kubernetes API clients, not arbitrary `kubectl`
  or shell execution.
- The initial product is local and loopback-only, not deployed in Kubernetes.
- v0.1 is read-only and has no Secrets, mutation, exec, attach, proxy,
  port-forward, remediation, or background collection path.
- Initial plugins are reviewed first-party modules built with the product;
  runtime downloads and third-party plugins are deferred.
- Console activity is not ForgeOps evidence until a separately approved strict
  artifact contract defines the boundary.

## Candidate sequence

The C labels are a parallel Console workstream and do not renumber the
published ForgeOps Milestones 066-088 or Workbench W1-W7 packages.

### C1 — Architecture and plugin boundary

**Purpose:** Improve the demonstration and prove trustworthiness.

Define the local core/browser boundary, explicit configuration behavior,
read-only v0.1 scope, plugin manifest and capability model, threat model,
versioning, failure behavior, and staged roadmap. Add executable documentation
policy tests without adding application code or cluster access.

### C2 — Offline walking skeleton

**Purpose:** Prove trustworthiness and prepare implementation.

**Status:** Complete and accepted through PR #98 at `72288e8`.

Create a loopback-only local core, static browser shell, strict configuration
loader seam, context-selection state machine, capability broker, and one inert
first-party example plugin. Use fixture configuration and Kubernetes fake
clients only.

Acceptance must prove no ambient kubeconfig, network, cluster, persistence,
credential disclosure, dynamic plugin, or mutation path. Technology and
dependency choices were reviewed before implementation. Published required-
workflow evidence and PR review passed before merge.

### C3 — Read-only resource browser

**Purpose:** Improve the demonstration.

**Status:** Complete and accepted through PR #100 at `4cf801b`.

Implement bounded namespace, Node, Deployment, ReplicaSet, Pod, Service, and
EndpointSlice views through first-party plugins and core-owned capabilities.
Show owner and selector relationships and exact context/namespace scope.

Offline fake-client acceptance precedes a separately approved read-only
SignalForge feasibility check. No general API discovery or ConfigMap values are
included.

### C4 — Logs, Events, and command explanation

**Purpose:** Improve the demonstration and prove trustworthiness.

Add bounded Events and Pod/container log reading, cancellation, stream limits,
control-character handling, sensitive-data warnings, and deterministic
equivalent-command previews. Preview text remains non-executable.

Acceptance must include oversized, hostile, stale-context, unavailable,
denied, disconnected, and cancellation cases.

### C5 — Reviewed ForgeOps evidence boundary

**Purpose:** Improve the incident-copilot demonstration and prove
trustworthiness.

Use an end-to-end operator exercise to identify the smallest Console output
that materially improves the accepted ForgeOps workflow. Design a strict,
versioned, bounded artifact or reject the integration if existing ForgeOps
commands are clearer.

The contract must preserve provenance limitations, explicit selection,
redaction, missing evidence, offline validation, and the absence of diagnosis
or remediation authority. Console activity records must not silently become
ForgeOps evidence.

### C6 — Plugin compatibility and distribution decision

**Purpose:** Prove trustworthiness and prepare a future release.

Evaluate the real first-party plugins to finalize SDK stability, compatibility
fixtures, lifecycle failure isolation, packaging, upgrades, and rollback.
Separately decide whether locally installed plugins add enough value to justify
publisher identity, signing, revocation, sandboxing, and supply-chain cost.

The acceptable decision is to retain built-in plugins only. A marketplace or
remote plugin loader is not presumed.

### C7 — Console release readiness and release

**Purpose:** Prepare a deliberate release.

Audit supported operating systems and Kubernetes versions, loopback security,
dependency locking, binaries and assets, provenance, update and rollback,
documentation, accessibility, installed-artifact acceptance, and the exact
plugin set. Choose a version only after the accepted scope is known.

No container image, in-cluster deployment, tag, or release is automatic. A
release stops if credential isolation, capability enforcement, installed
behavior, or rollback is not independently demonstrated.

## Conditional candidates

| Candidate | Admission evidence required |
| --- | --- |
| Metrics plugin | A defined incident question needs Metrics Server or Prometheus data not already visible in the resource workflow |
| Helm plugin | A demonstrated operator workflow needs release/revision context and its credential boundary is understood |
| Workbench integration | Selected live resource YAML needs browser-local inspection and a strict transfer boundary is designed |
| Write operations | A concrete repeated operator need outweighs the mutation, confirmation, recovery, and audit risk |
| In-cluster deployment | Multiple users require shared access and OIDC, TLS, RBAC, storage, and upgrade ownership are accepted |
| Third-party plugins | Built-in plugins prove a stable SDK and external extensibility justifies signing, sandboxing, revocation, and support |

## Success measure

The Console succeeds when an operator can more quickly understand a bounded
cluster condition, see exactly what was requested, and intentionally carry
reviewed evidence into the deterministic incident-copilot workflow without
expanding ForgeOps authority. More resources, buttons, plugins, or commands do
not demonstrate success by themselves.
