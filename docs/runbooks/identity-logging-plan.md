# Forge central logging priorities

**Status: prioritized next platform work, not deployed. Reviewed 2026-09-30.**

Operator decision: expand searchable logs for the main Forge applications before
implementing the proposed identity backup cadence. The bounded recovery
namespace cleanup completed September 30 at 16:02 EDT, with original Dex and API
health checks passing. Existing retained backups remain protected; deferral
does not establish a backup schedule or a guaranteed recovery point.

The repository's [Alloy configuration](../../k8s/central-logging/alloy-config.yaml)
discovers only `forge-pulse`; its [RBAC](../../k8s/central-logging/alloy-rbac.yaml)
permits Pod discovery and Pod-log reads only there. The accepted Loki rollout
therefore does not establish collection of API-server, Dex, Headlamp or gateway
logs. Confirm live configuration before any rollout; repository intent is not a
fresh live readback. See the [incident](../incidents/2026-09-30-headlamp-oidc-signature-rejection.md).

## Sequenced coverage

| Priority | Sources | Acceptance |
| --- | --- | --- |
| 1 — Identity and entry | API server, Dex, Headlamp, Traefik | Find a known benign line per source and safely classify an authentication failure; preserve existing Pulse collection |
| 2 — Main applications and observability | ForgeOps Console, portal, Restaurant API, YAML Workbench; Grafana, Prometheus, Loki and Alloy | Search each emitting container by namespace/pod/container; identify deliberately quiet apps; measure log volume and collector health |
| 3 — Platform dependencies | CoreDNS, controller manager, scheduler, cert-manager, Calico/Tigera, MetalLB; Istio control plane and learning lab | Scoped error correlation, namespace RBAC review and resource/capacity acceptance |
| Separate follow-up | Kubernetes Events and host kubelet/containerd journals | Reviewed event permissions and host access; prove collection behavior during API unavailability |

Roll out incrementally. Do not grant cluster-wide logs access merely to avoid
listing namespaces. Admission, API discovery, network access and source-specific
sensitive-data review must pass for each increment. No application is claimed
covered until a known record is found in Loki. Quiet services need an approved
benign request or other coverage evidence, not a fabricated error in production.

Create a coverage table during rollout: namespace, workload/container, collection
method, last verified timestamp, sample/query reference, retention limit and
known gaps. This makes missing logs visible before an incident. Application logs,
gateway access logs, Kubernetes Events and audit records are separate data types.
For Loki/Alloy's own failure, keep direct Pod logs as a fallback; self-observation
through an unavailable Loki cannot be the only diagnostic path.

## First increment details

| Source | Purpose | Boundary |
| --- | --- | --- |
| kube-system / kube-apiserver | OIDC verification errors | Select only API-server targets; explicitly review namespace log-read permission |
| forge-identity / Dex | Provider startup, storage and sign-in failures | Never collect exported signing keys or configuration Secrets |
| forge-headlamp / Headlamp | Callback and upstream API failures | Scrub token/cookie/client-secret material before ingestion |
| forge-gateway / Traefik | Distinguish gateway challenges from upstream failures | Ordinary logs first; access logging is a separate reviewed configuration |

Use namespace-scoped Roles rather than cluster-wide log-read privileges. A
collector target filter narrows collection but is **not** an RBAC security
boundary: namespace-wide `pods/log` permission can still read other Pods there.
Keep namespace/pod/container labels; add no token, email, authorization code or
full request URL as labels. Preserve useful info/warning context, not only lines
containing `error`. Store and display timestamps consistently (UTC or explicit
EDT conversion). Review Loki access and volume growth against its 8 GiB volume.

If access logs are needed, allowlist method, path without query string, status,
router/service and timing fields. Drop Authorization, Cookie, Set-Cookie, query
strings and request/response bodies. Callback query strings can contain codes.
Test redaction using synthetic markers before enabling the source; regex-only
redaction is not proof that arbitrary secrets cannot leak. Do not enable verbose
OIDC payload logging. Kubernetes audit bodies/TokenReview requests are outside
this first increment.

## Queries after collection is verified

In Grafana Explore, select SignalForge Loki and an explicit incident time range:

```logql
{namespace="kube-system", container="kube-apiserver"} |= "failed to verify id token signature"
```

```logql
{namespace=~"forge-identity|forge-headlamp|forge-gateway"} |~ "(?i)(oidc|unauthorized|authentication|error)"
```

These are planned queries, not evidence that historical September 30 logs are in
Loki. New collection does not guarantee backfill. Empty results can mean missing
collection, wrong labels/time range, expired retention, or genuinely no matches.
Logs would likely have located the signature failure sooner, but TokenReview and
local cryptographic verification were still needed to isolate the failure.

## Rollout acceptance and fallback

1. Capture live Alloy config/RBAC, Loki disk usage and current ingestion baseline.
2. Render the pinned Alloy version's config and validate it; review exact namespace
   permissions and target selection. Preserve existing Pulse collection.
3. Check synthetic sensitive-data filtering and access controls before deployment.
4. Dry-run/diff named resources, then perform a scoped operator-reviewed rollout.
5. Match a known benign line and timestamp from each source in Loki; verify denied
   access outside selected namespaces and verify original Pulse ingestion continues.
6. Observe collector CPU/memory, dropped logs, reconnects and Loki disk growth.
   Record measured retention/recovery limits; seven-day retention is not yet proven.
7. On failure restore captured Alloy config/RBAC and verify Pulse collection;
   retain Loki storage. No whole-directory apply or PVC deletion.

API-based collection depends on Kubernetes and can have gaps during an API outage.
Alloy's current state directory is `emptyDir`; collector replacement is not proof
of gap-free replay. Keep direct `kubectl logs --previous` and SSH/runtime/journal
fallbacks. A later host-file/journal collector would reduce API dependency but
needs its own host-access and security review. Kubernetes Events also need a
separate collector and RBAC; Pod stdout collection does not automatically ingest
Events. No host collector, Events pipeline, new alerts or automation is installed
by this plan.

References: [Alloy Kubernetes log source](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/),
[Events source](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes_events/).
Validate features against the deployed Alloy version before applying examples.
