# ForgeOps Console plugin contract

**Status:** C1 design contract; no plugin runtime is implemented

## Design objective

The plugin contract should let Console features evolve without granting each
feature direct access to kubeconfig credentials, Kubernetes clients, browser
transport internals, or ForgeOps authority. The initial model is a versioned
SDK for first-party modules compiled and released with the Console.

Plugins provide contributions. The trusted core provides capabilities.

## Manifest shape

The proposed initial manifest uses a strict schema:

~~~yaml
apiVersion: console.forgeops.io/v1alpha1
kind: ConsolePlugin
metadata:
  id: forge.logs
  displayName: Logs and Events
spec:
  version: 0.1.0
  sdkCompatibility: ">=0.1.0 <0.2.0"
  capabilities:
    - pods.read
    - pods.logs.read
  contributes:
    resourcePanels:
      - id: pod-logs
        resource: pods
        title: Logs
    actions:
      - id: pod-logs-tail
        resource: pods
        capability: pods.logs.read
~~~

The final schema and compatibility grammar remain C2 implementation decisions.
The following invariants are fixed by C1:

- `apiVersion`, `kind`, plugin ID, plugin version, SDK compatibility, requested
  capabilities, and contributions are mandatory and strictly validated;
- unknown fields fail validation rather than being ignored;
- plugin IDs and contribution IDs are unique and stable;
- a contribution references only capabilities declared by that plugin;
- declaring a capability does not grant it; the core must support it and the
  selected Kubernetes identity must still be authorized;
- a plugin cannot declare arbitrary Kubernetes resources, API paths, verbs, or
  shell commands; and
- manifest text contains no credentials, kubeconfig data, executable URLs, or
  inline executable code.

## Core capability model

Each capability is a versioned core-owned operation with:

- a stable identifier;
- a strict structured request and response schema;
- fixed Kubernetes resource, subresource, and verb mappings;
- parameter, result, byte, item, duration, and concurrency bounds;
- disclosure and redaction behavior;
- cancellation behavior;
- an equivalent-command renderer when one is honest and useful; and
- activity-record semantics.

Candidate read-only v0.1 capability families are:

| Family | Examples |
| --- | --- |
| Context | `contexts.list`, `contexts.select`, `namespaces.list` |
| Workloads | `deployments.list`, `deployments.read`, `replicasets.read`, `pods.read` |
| Relationships | `owners.read`, `selectors.resolve` |
| Networking | `services.read`, `endpointslices.read` |
| Events | `events.list`, `events.watch` |
| Logs | `pods.logs.read`, `pods.logs.follow` |
| Explanation | `command.preview`, `capability.describe` |

Mutation and interactive process capabilities are not reserved placeholders in
v0.1. They require a future contract and cannot be enabled by a manifest-only
change.

## Contribution types

The initial SDK may expose these extension points:

- navigation page;
- dashboard card;
- resource-list column;
- resource-detail panel;
- contextual action;
- command-builder template;
- evidence candidate renderer; and
- settings panel containing non-secret plugin preferences.

Every contribution is namespaced by plugin ID, mounted in an explicit core
slot, and supplied only the minimum typed data required for that slot. Plugins
cannot replace the persistent context banner, permission disclosure, activity
view, error boundary, or confirmation surface.

## Lifecycle

The proposed lifecycle is deterministic:

1. discover the build-time registry;
2. validate every manifest before starting the listener;
3. reject the complete startup on duplicate identity or an invalid required
   built-in plugin;
4. register declared contributions against supported SDK slots;
5. resolve requested capabilities against the core allowlist;
6. show unavailable contributions as unavailable or omit them according to one
   tested rule; and
7. isolate runtime plugin errors without changing the active context or
   crashing unrelated features.

Plugin initialization must not access a kubeconfig, open a Kubernetes client,
contact a network service, write persistent state, or start background work.

## Versioning and compatibility

- The SDK follows semantic versions independently from Console product and
  ForgeOps package versions.
- A plugin declares a bounded SDK compatibility range.
- The loader rejects an incompatible major or pre-release contract.
- Removing or changing a capability schema requires an SDK major version.
- Adding an optional contribution field may use a minor version only when old
  loaders reject it clearly rather than misinterpret it.
- Plugin contract fixtures and a compatibility matrix are release inputs.
- ForgeOps evidence schema compatibility is a separate decision and must not
  be inferred from Console SDK compatibility.

## Testing contract

The future SDK test harness should let a plugin prove:

- manifest validity and uniqueness;
- exact requested capabilities;
- rejection of undeclared and unknown capability calls;
- rendering with permitted, denied, missing, malformed, oversized, cancelled,
  and timed-out responses;
- cleanup of streams and subscriptions;
- accessible keyboard and error behavior;
- no credential, Secret, or hidden mutation path; and
- compatibility with every declared supported SDK version.

The core test suite must include a deliberately invalid plugin and a plugin
that throws during each lifecycle phase. One plugin's failure must not silently
broaden another plugin's capabilities or change context state.

## Deferred distribution model

Installed packages, signatures, third-party plugins and publishers, a catalog,
automatic updates, and runtime enable/disable are deferred. Before any is implemented, a
separate decision must cover package integrity, publisher identity, review,
revocation, offline installation, rollback, sandboxing, update failure, and
the risk of executing plugin code with the operator's local identity.

Until that decision, “plugin” means a reviewed first-party module compiled and
tested with the Console release.
