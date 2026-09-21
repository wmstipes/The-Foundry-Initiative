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

Required GitHub validation and dependency review remain pending publication.
The separately gated SignalForge read-only feasibility check has not been
authorized or performed.

## Gate status

1. Projection, limit, and generation contract — approved and implemented.
2. Hardened client and scope lifecycle — approved and implemented.
3. Core read capabilities and relationships — approved and implemented.
4. Compiled resource plugin and synthetic browser demo — approved and
   implemented; local smoke exercise passed.
5. Adversarial, race, build, audit, repository, and required CI validation —
   local checks passing; publication and required CI pending.
6. Review, merge, reconciliation, and cleanup — pending Gate 5 publication.
