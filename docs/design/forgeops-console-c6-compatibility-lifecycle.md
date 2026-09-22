# Console C6 — compiled compatibility and lifecycle

## Scope and implementation status

This change follows planning PR #107 and the focused source assessment of main
`45c6c7e`. It retains three compiled first-party plugins. There is no admitted
need for runtime third-party loading, a marketplace, general semantic-version
negotiation, or separate plugin installation. This is a review candidate, not a
public Console release or acceptance of every C6 gate.

ForgeOps v1.0.0 remains unchanged. C5's observation contract remains a design:
no exporter, candidate validator, or ForgeOps intake is added. EKS authentication,
Istio and ForgeFire retain their separate scope and authority requirements.

## Actual supported set

All plugin versions and the SDK are `0.1.0`. The only accepted manifest SDK
compatibility value remains the literal `>=0.1.0 <0.2.0`.

| Plugin | Capabilities | Contribution ID / type |
| --- | --- | --- |
| `forge.example` | `example.status` | `example.card` / `dashboardCard` |
| `forge.resources` | `resources.read` | `resources.browser` / `resourceBrowser` |
| `forge.diagnostics` | `pods.logs.read`, `events.read`, `command.preview` | `diagnostics.pod` / `resourceBrowser` |

The diagnostic contribution identifies `pods.logs.read`; its built-in view also
uses the other two separately brokered capabilities. Context/namespace/session
HTTP endpoints belong to the core, not extra manifest capabilities.

The registry validates declarations, rejects duplicate plugin IDs and copies
manifest slices on ingress/egress. The broker rejects missing, undeclared and
unregistered capabilities, and startup now checks every declared handler exists.
HTTP routes bind fixed plugin identities and operation-specific capabilities.
The browser validates the supported plugin versions, capabilities and
contributions; a missing compiled card is visible rather than silently omitted.

These are contracts for trusted compiled code. An in-process Go module could
bypass an API it is supposed to use, and same-origin JavaScript shares browser
authority. Manifest identifiers are not caller authentication or a sandbox.
No process isolation or arbitrary third-party safety is claimed.

## Source pairing and version policy

`bundle.go` embeds bounded, explicit Console source inputs and computes a
SHA-256 fingerprint of their sorted relative paths and bytes. Vite computes the
same fingerprint, compiles it into the browser, and emits `forgeops-bundle.json`.
The protocol identity is `forgeops.console/v1alpha1`.

Before listening, the core requires the asset manifest to match its embedded
identity. Bootstrap includes that identity, and the browser rejects mismatched
identity or unsupported contributions before retaining the session nonce.
Missing, malformed or mismatched assets produce a clear startup error. Rebuild
both halves after source changes, including changes to included test files.

The fingerprint is exact source-input pairing, not compiled-byte verification,
publisher authentication, a signature, or proof of an uncompromised toolchain.
It covers the explicitly named Console input set, not every repository file.
The trusted asset directory must not be modified while running. A person able
to replace assets and forge their manifest is outside this check's protection.
Release checksums, signed provenance if admitted, supported operating systems,
and installed release acceptance remain C7 decisions.

A plugin capability/contribution or protocol change must update the reviewed
supported set and its compatibility tests. Arbitrary patch/minor range
negotiation is not supported. A shared version label alone does not substitute
for the source fingerprint. Mixed old/new assets are rejected by the new core;
older cores predating this check cannot provide the same startup guarantee.

## Resource completeness and browser state

Primary pagination, supporting Pod/EndpointSlice pagination and count limits,
and clipped relationships propagate an incomplete result. Individual reads
retain incompleteness. This is conservative: a limited supporting list can mark
all returned relationships potentially incomplete even if an omitted object
would not have matched. No additional pages or broader reads are introduced.
An absent displayed relationship is not proof of absence in the cluster.

Resource changes clear previous objects and selections before fetching. Context
activation clears namespace choices, and incomplete namespace discovery is
visible. Resource requests carry AbortSignal and are checked for operation,
kind and generation; the view also checks context and namespace. Unmounting
invalidates pending work. Core scope-generation checks remain the authority.
This does not provide automatic synchronization between multiple browser tabs;
a tab can display an older snapshot, and stale requests are rejected by core.

## Failure and teardown behavior

| Failure | Implemented behavior | Limit |
| --- | --- | --- |
| Invalid manifest, missing handler or mismatched assets | Startup fails before listening | Not a general plugin discovery system |
| Undeclared/unknown capability | Fixed denial | Not process isolation |
| Expected upstream failure | Sanitized status/code, no partial diagnostic content | Logs/Events themselves are not guaranteed redacted |
| Synchronous diagnostic panic | Empty result, `internal_error`, failure activity | No raw panic value is returned |
| Other synchronous broker panic | Empty response, fixed internal error | No arbitrary goroutine panic recovery |
| Scope change or browser cancellation | Cooperative cancellation; diagnostics close streams | Cannot forcibly stop arbitrary Go code |
| Shutdown | Close session, cancel active scope, await drain for up to five seconds, then close transport on deadline | A noncooperative handler may remain until process exit |
| Browser render exception or process crash | No new isolation mechanism | Not claimed contained by broker recovery |

Shutdown now joins cleanup before the executable returns. Session close is
idempotent and permanently rejects new scope work. A resource operation whose
context was cancelled before its final result check cannot report success.
The diagnostics activity recorder recovers before classifying outcome, avoiding
an `ok` entry followed by a misleading authorization error.

## Build, upgrade and rollback procedure

1. Use one clean source revision and the locked Go/Node dependencies. Build the
   browser and both required Go entry points from that same source tree.
2. Keep each candidate executable and complete browser directory together in a
   separate directory. Preserve the previous pair until acceptance is complete.
3. Stop the running Console, then launch the new pair using its explicit asset
   directory. Production kubeconfig selection remains explicit and unchanged.
4. Verify the pair with the synthetic demo before any separately authorized
   live use. Bootstrap identity and plugin inventory must match.
5. To roll back, stop the candidate and restore the previous executable and
   complete browser directory together. Start a new in-memory session and
   explicitly reselect context and namespace. There is no persistent application
   state migration in this change.

A synthetic mismatched-identity rejection and restoration of the valid pair
exercise the pairing mechanism, not acceptance of an unbuilt historical release.
Do not publish public binaries or claim Windows/live acceptance from Linux
synthetic checks.

## Evidence and remaining work

See the [testing inventory](../testing-and-validation.md) for executed suites,
and the [C6 gate record](../milestones/forgeops-console-c6-plugin-compatibility-planning.md)
for review/merge boundaries. Tests are selected for the specific source findings:
relationship incompleteness, stale selections, panic reporting, shutdown drain,
and mismatched bundles. No tests merely assert this document's prose.

The existing ambiguous Node Scheduling label (C3-UX-01), unsupported-auth error
specificity, C5 aligned operator acceptance and future evidence export remain
open. Standard EKS credentials are still rejected and may produce a generic
unavailable result; this change does not introduce cloud authentication.
