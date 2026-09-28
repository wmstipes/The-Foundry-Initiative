# Forge LAN portal and private HTTPS

The gateway is LAN-only. MetalLB v0.16.1 runs in native L2 mode and announces
`192.168.243.250` for the Traefik v41.6.0 LoadBalancer Service in
`forge-gateway`. Firewalla's DHCP allocation currently ends at
`192.168.243.235`; `.249`–`.251` were checked unleased before the pool was
created. The single-address pool has `autoAssign: false` to prevent accidental
allocation to another Service. The Traefik dashboard route is disabled.

The portal uses a small, restricted, stateless HTTP server with two replicas.
Traefik terminates private HTTPS using the `forge-gateway-tls` Secret in its
`default` TLSStore, backed by the offline-root private CA. Port 80 redirects to
HTTPS with a temporary 302. The portal links to the Workbench and Restaurant
API over HTTPS. Do not enter sensitive YAML in the demo Workbench; it has no
application login. Grafana has its own login; Prometheus has a LAN BasicAuth
gate. Headlamp and Service Pulse now have active portal cards and their own
BasicAuth-protected HTTPS routes; the Headlamp sign-in additionally uses Dex
OIDC. Their Services remain ClusterIP. The Service Pulse probe remains
internal. The Headlamp and Pulse board ingress policies permit the gateway
selectors; see the [protected route runbook](protected-apps.md) for acceptance
and scoped route removal.
The ForgeOps Console card points to the protected cluster pilot. Its anonymous
`401` and fresh private-browser authentication prompt passed on 2026-09-27.
See [the cluster runbook](../forgeops-console/README.md) for its single-operator
scope and access limits.

## Install / reconcile

Run from the repository root using PowerShell:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --context $ctx -f .\k8s\lan-portal\namespace.yaml
kubectl apply --dry-run=server --context $ctx -f .\k8s\lan-portal\portal.yaml
kubectl apply --context $ctx -f .\k8s\lan-portal\portal.yaml
kubectl rollout restart deployment/forge-portal -n forge-portal --context $ctx
kubectl rollout status deployment/forge-portal -n forge-portal --context $ctx --timeout=120s
kubectl get pods,service,ingress -n forge-portal --context $ctx
```

Apply the namespace first so the server-side dry run can validate the
namespaced resources against the restricted Pod Security policy.

To reconcile MetalLB separately, run
`kubectl apply --context $ctx -f .\k8s\lan-portal\metallb-pool.yaml`.
Install/upgrade Traefik separately with the pinned chart and
`--values .\k8s\lan-portal\traefik-values.yaml`. Keep the chart release,
namespace, and VIP stable. A chart upgrade must be reviewed against the
currently installed version before applying.

## Client hosts entries

Add the following entries to the Windows hosts file on the laptop and NUC,
`C:\Windows\System32\drivers\etc\hosts` (edit as Administrator):

```text
192.168.243.250 forge.home.arpa
192.168.243.250 yaml.forge.home.arpa
192.168.243.250 restaurant.forge.home.arpa
192.168.243.250 grafana.forge.home.arpa
192.168.243.250 prometheus.forge.home.arpa
192.168.243.250 forgeops.forge.home.arpa
```

This historical bootstrap list omits the subsequently activated protected
cards and Dex; maintain their name resolution in the private operator notes
on each client that needs access.

The `home.arpa` suffix is reserved for home networks. Browser entry point:
`https://forge.home.arpa/`. Install the **public** root certificate into each
client's CurrentUser Root store after comparing its SHA-256 with the expected
`68105417902A1EF6C0905DF6923774E0DEB3BB59EAF83B21E1E41651CB874106`.
Never import the root private key on a client. Windows curl (Schannel) can
report unknown revocation status for the private CA, which has no online
revocation endpoint; `--ssl-revoke-best-effort` still checks chain and hostname.
For a one-off check before trusting the root, set `$caFile` to the path of
the exported public root `.crt`, then use
`curl.exe --ssl-revoke-best-effort --cacert $caFile --resolve forge.home.arpa:443:192.168.243.250 https://forge.home.arpa/`.
The portal is only available
while the cluster, gateway speaker, and LAN are functioning; the single
control-plane node remains a single point of failure.

## Next stage

Install the public root on the NUC after verifying the hash and supplying
local hostname resolution for the protected applications and Dex. The
additional routing and identity details are retained in private operator
material outside Git. Prometheus access and recovery are described in
[its runbook](prometheus-private-access.md). Keep Headlamp's read-only
authorization and its private OIDC overlay when upgrading it.
