# Identity and control-plane logging plan

**Status: proposed, not deployed. Reviewed 2026-09-30.**

The repository's [Alloy configuration](../../k8s/central-logging/alloy-config.yaml)
discovers only `forge-pulse`; its [RBAC](../../k8s/central-logging/alloy-rbac.yaml)
permits Pod discovery and Pod-log reads only there. The accepted Loki rollout
therefore does not establish collection of API-server, Dex, Headlamp or gateway
logs. Confirm live configuration before any rollout; repository intent is not a
fresh live readback. See the [incident](../incidents/2026-09-30-headlamp-oidc-signature-rejection.md).

## Proposed first increment

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
