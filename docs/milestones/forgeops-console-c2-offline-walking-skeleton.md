# ForgeOps Console C2 — offline walking skeleton

## Purpose

C2 turns the accepted C1 boundary into the smallest executable Console shape.
It proves that a local Go core and React browser shell can exchange sanitized
state through a constrained plugin capability without granting Kubernetes or
host authority.

## Implementation outcome

The C2 candidate contains:

- a Go 1.27 loopback server built on `net/http`;
- an explicit, regular-file-only kubeconfig loader with a 1 MiB bound;
- sanitized, sorted context summaries and in-memory-only context selection;
- exact Host and Origin checks plus a random in-memory session nonce for state
  changes;
- a versioned compiled plugin manifest and contribution contract;
- a deny-by-default, typed capability broker with cancellation and panic
  containment;
- one compiled `forge.example` dashboard card whose only capability returns a
  fixed offline status;
- a React 19 and TypeScript browser shell with visible offline scope and no
  browser persistence; and
- fixture, unit, policy, build, audit, and CI coverage.

## Exact technology baseline

| Layer | C2 choice |
| --- | --- |
| Core | Go 1.27, standard `net/http` |
| Kubernetes types and fake-client dependency | `client-go` 0.36.4 |
| Browser | React and React DOM 19.3.0 |
| Language and build | TypeScript 7.0.2 and Vite 8.3.0 |
| Browser tests | Vitest 5.0.1 with Happy DOM 20.14.5 |
| Runtime | Node.js 24 LTS in required validation |

Go module and npm lock data define the exact transitive graphs. No router,
state library, UI kit, CSS framework, dynamic plugin loader, or embedded
browser runtime is introduced.

## Trust boundaries proved

- Only a caller-supplied kubeconfig path is read. Environment, home-directory,
  and in-cluster configuration fallbacks are absent and tested.
- Kubeconfig credentials remain core-side. Browser bootstrap data contains only
  context, cluster, auth-info, and namespace labels.
- The listener rejects hostnames, wildcard addresses, and non-loopback IPs.
- Browser state changes require an unpredictable nonce held only in memory.
- Plugin manifests are compiled, strictly validated, and matched to registered
  handlers. Unknown plugins, undeclared capabilities, and unregistered handlers
  are denied.
- The production Kubernetes client factory returns `ErrOfflineOnly`; a test-only
  injected `client-go` fake proves the seam without a network request, and C2
  never uses the fixture server address.
- Selecting a context changes only process memory and does not change the
  kubeconfig's `current-context` field or any file.

## Explicit exclusions

C2 performs no live cluster feasibility check and includes no resource read,
logs, Events, watch, stream, mutation, exec, attach, proxy, port-forward,
arbitrary API path, Secret access, persistence, dynamic plugin, package,
container image, manifest, deployment, tag, or release. These exclusions are
not incomplete C2 features; they preserve the separately gated C3 and later
boundaries.

## Validation evidence

The candidate defines 24 Go test functions across configuration, session,
plugin, broker, server, and offline-client boundaries; two browser API tests;
and ten repository policy tests. Required Validation runs Go tests and vet,
browser tests and production build, a production dependency audit, the complete
Python suite, and existing repository gates.

Local browser validation passed with Vitest 5.0.1, Vite 8.3.0, Node.js 24, and
zero reported production dependency vulnerabilities. Go execution and the
complete repository result are recorded from the published required workflow
because the implementation environment does not provide a Go toolchain.

## Gate status

1. C2 admission and technology selection — approved by Mike.
2. Explicit configuration and in-memory context boundary — approved and
   implemented in the candidate.
3. Plugin manifest and deny-by-default broker — approved and implemented in the
   candidate.
4. Loopback HTTP and browser shell boundary — approved and implemented in the
   candidate.
5. Offline and regression validation — approved; final published workflow
   evidence pending.
6. Review, merge, reconciliation, and cleanup — approved; pending successful
   final-head validation and Mike's PR review.

C3 remains separately gated. C2 acceptance does not authorize a Kubernetes
client, cluster request, resource browser, or live feasibility check.
