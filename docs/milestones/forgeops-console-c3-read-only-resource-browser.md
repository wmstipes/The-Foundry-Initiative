# ForgeOps Console C3 — read-only resource browser

## Purpose

C3 creates the first useful Console demonstration: a bounded browser view of
common Kubernetes resources and their owner or selector relationships. It does
not add command execution, logs, Events, mutation, dynamic plugins, or ForgeOps
evidence authority.

## Implemented outcome

- fixed projections for Namespace, Node, Deployment, ReplicaSet, Pod, Service,
  and EndpointSlice objects;
- exact context, namespace, and monotonically increasing generation shown in
  the browser;
- stale-request cancellation and stale-response rejection after every scope
  change;
- five-second request timeout, four-query concurrency cap, 200-object list
  bound, 1 MiB projected-response bound, and 100-entry metadata-only activity
  history;
- a compiled `forge.resources` first-party plugin with one brokered
  `resources.read` capability;
- a production typed client factory that rejects ambient configuration, exec
  and auth-provider plugins, secondary credential files, proxies, insecure
  TLS, and impersonation; and
- a separate `forgeops-console-demo` binary populated only by hard-coded fake
  client objects and permanently labeled as synthetic.

## Disclosure boundary

The core returns only named projection fields. It never serializes Kubernetes
API objects. Annotations, managed fields, ConfigMap values, Secrets, Events,
container environment, logs, tokens, certificates, and upstream error text are
absent. Error responses use a fixed vocabulary: `invalid_request`,
`namespace_required`, `stale_scope`, `unauthenticated`, `forbidden`,
`not_found`, `timeout`, `too_large`, and `unavailable`.

The request contract accepts only `list` or `read`, one of seven exact resource
identifiers, the current generation, and an object name only for `read`. It has
no arbitrary verb, API path, group/version/resource, selector, field selector,
or query-string surface.

## Local validation evidence

The candidate passes Go formatting, locked `go mod tidy`, all 31 Go tests,
`go vet`, and all Go tests under the race detector. The browser passes four
Vitest tests, TypeScript compilation, and the Vite production build. All 244
top-level Python unittest cases pass, including 15 Console policy cases.

An HTTP demo smoke exercise used only `forgeops-console-demo`. It verified the
`synthetic-demo` mode, both compiled plugin manifests, two projected
namespaces, explicit generation changes from context to namespace, a bounded
Deployment projection, and two selector-derived Pod relationships. No
kubeconfig was loaded and no network target beyond the loopback demo server was
contacted.

Published-head Required Validation run `35639420344`, ForgeOps CI run
`35639420138`, and Repository Security Validation run `35639420345` completed
successfully. Required Validation included dependency review, the locked Go
module graph, Go formatting/tests/vet, browser tests/build/audit, the 253-test
Python discovery, repository validators, and its aggregate gate.

PR #100 merged at `4cf801b5d3a1e285834646880193152a9da6dc2b`.
Its published head `be773da3c694e545165c42f727ab7fcbca3f7098`,
merge commit, and locally reviewed commit share exact tree
`8a97af8fdd0c01e55c7c2fef3624a2652b0bcbc5`. GitHub removed the remote
implementation branch after merge. At implementation closeout, the separately
gated SignalForge read-only feasibility check had not been authorized or
performed. The later authorized walkthrough is recorded below.

## Live read-only walkthrough — 2026-09-21

The operator explicitly authorized the bounded read-only C3 check against
SignalForge, then ran the production Console locally on Windows from accepted
main `82741388f6b2c79a381ac35b6c7bf4e4ecbf90b5` (C3 closeout PR #101).
Evidence consists of operator-supplied terminal output and browser screenshots
reviewed in the working conversation, not an independently executed cluster
audit or a signed runtime provenance record. No screenshot or credential file
is included in this documentation change.

Laptop prerequisites were Go 1.27.1, Node 24.19.0, and npm 11.17.0. `npm.cmd ci`
reported zero vulnerabilities; all four Vitest API tests, the production web
build, `go test ./...`, and the production Go binary build passed. Using
`npm.cmd` avoided changing PowerShell execution policy.

The operator supplied an explicit existing kubeconfig path and selected context
`kubernetes-admin@kubernetes`. The production server listened only on
`127.0.0.1:9090`. The selected workload namespace was `forge-restaurant`.
The context name does not establish least-privilege credentials: this check
exercised the Console's bounded read-only surface, not an RBAC restriction test.

| View or interaction | Observed result |
| --- | --- |
| Context and namespace | Explicit activation and namespace selection produced generation 2; namespace discovery returned nine items. |
| Deployments | `restaurant-api`: desired/current/ready/available replicas all 3; selector relationships listed three Pods. |
| ReplicaSets | Six listed; selected active `restaurant-api-6dfbf8dd9b` had all four replica counts at 3, Deployment ownership, and three Pod relationships. Five other entries showed 0/0 ready. |
| Pods | Three listed Running; selected Pod ending `4nnlb` showed 1/1 ready, zero restarts, node `forge-node-01`, container `restaurant-api`, and the active ReplicaSet owner. Other Pods' individual details were not inspected. |
| Services | ClusterIP and NodePort Services listed; selected `restaurant-api` showed `http 80/TCP`, three selected Pods, and its EndpointSlice relationship. |
| EndpointSlices | Two listed at 3/3 ready; selected `restaurant-api-9wtr7` showed IPv4, `http 8000/TCP`, and owner/relationship links to `restaurant-api`. |
| Nodes | All four nodes showed `Ready=True`; selected `forge-head` showed control-plane role, kubelet v1.36.4, and capacity of 4 CPUs, 16599408Ki memory, and 110 Pods. Capacity is not usage. |
| Scope reset | Reactivating the same context advanced generation 2 to 3, cleared namespace and Pod results/details, and visually disabled namespaced controls. Historical activity remained labeled with its original generation. |
| Scope reselection | Explicitly setting `forge-restaurant` advanced generation to 4; a successful generation-4 request returned three Running Pods and restored selected Pod details. |

Disposition: the bounded live resource-browser happy path and visible scope
reset/reselection passed. This does not prove concurrent stale-response
rejection or in-flight cancellation, every authorization/error/limit path,
continuous cluster health, or Service/application network reachability.
No logs, Events, exec, commands, mutation, deployment, or application endpoint
checks were part of the walkthrough. Stopping the local server was requested;
shutdown confirmation was not supplied with the evidence above.

## Open usability follow-up

**C3-UX-01 — Node scheduling label (open; implementation deferred).** The Node
projection labels `spec.unschedulable` as `Scheduling`, so the observed value
`false` is ambiguous. It means the unschedulable flag is false, not that
scheduling is disabled; it does not guarantee that a particular Pod can run
there. A future approved patch should label the flag explicitly (for example,
`Unschedulable`) or present a clear cordon state, with regression coverage for
both boolean values. This reconciliation changes no application code.

C4 remains separately gated and unstarted; this walkthrough does not authorize
logs, Events, or any expanded live operation.

## Gate status

1. Projection, limit, and generation contract — approved and implemented.
2. Hardened client and scope lifecycle — approved and implemented.
3. Core read capabilities and relationships — approved and implemented.
4. Compiled resource plugin and synthetic browser demo — approved and
   implemented; local smoke exercise passed.
5. Adversarial, race, build, audit, repository, and required CI validation —
   passed on the published accepted head.
6. Review, merge, reconciliation, and cleanup — complete through PR #100 and
   this closeout reconciliation.
