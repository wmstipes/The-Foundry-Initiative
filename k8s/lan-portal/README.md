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
application login. Grafana has its own login; Prometheus has a LAN BasicAuth gate. Both use
HTTPS ingress while their Services remain ClusterIP. Headlamp and Service
Pulse remain unlinked until protected access is in place.
The ForgeOps Console card links to its setup instructions. Console currently runs
on the operator workstation with a loopback-only listener; the card is not an
in-cluster Console endpoint and does not launch the app. An always-on Console
would need a separate Kubernetes deployment and authentication design.

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
```

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

Install the public root on the NUC after verifying the hash, then add
protected ingress routes for Headlamp and Service Pulse only after checking
authentication and authorization. Prometheus access and recovery are described
in [its runbook](prometheus-private-access.md). Headlamp must retain
read-only privileges and must not use an unprotected service-account-token
auto-login.
