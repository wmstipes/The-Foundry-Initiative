# Forge LAN portal (first stage)

The gateway is LAN-only. MetalLB v0.16.1 runs in native L2 mode and announces
`192.168.243.250` for the Traefik v41.6.0 LoadBalancer Service in
`forge-gateway`. Firewalla's DHCP allocation currently ends at
`192.168.243.235`; `.249`–`.251` were checked unleased before the pool was
created. The single-address pool has `autoAssign: false` to prevent accidental
allocation to another Service. The Traefik dashboard route is disabled.

The initial portal uses a small, restricted, stateless HTTP server with two
replicas. It contains links to the Workbench and Restaurant API. The ingress
routes expose those two preexisting public demo workloads over HTTP on the
LAN. Do not put credentials in those pages or enter sensitive YAML while this
HTTP stage is in use. Headlamp, Grafana, Prometheus, and Service Pulse remain
ClusterIP-only until private HTTPS and appropriate authentication are in place.
The portal labels those entries as pending instead of providing broken links.

## Install / reconcile

Run from the repository root using PowerShell:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --dry-run=server --context $ctx -f .\k8s\lan-portal\portal.yaml
kubectl apply --context $ctx -f .\k8s\lan-portal\portal.yaml
kubectl rollout status deployment/forge-portal -n forge-portal --context $ctx --timeout=120s
kubectl get pods,service,ingress -n forge-portal --context $ctx
```

The namespace in `portal.yaml` must be created before its namespaced objects
on clusters that reject a single multi-document apply across a new namespace.
If that happens, run
`kubectl apply --context $ctx -f .\k8s\lan-portal\portal.yaml --dry-run=client`
for syntax validation, then apply the Namespace document separately and retry.
For existing clusters the namespace is already present after the first apply.

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
```

The `home.arpa` suffix is reserved for home networks. Browser entry point:
`http://forge.home.arpa/`. Before updating hosts files, verify routes with
`curl.exe --resolve forge.home.arpa:80:192.168.243.250 http://forge.home.arpa/`
and the equivalent names for the two linked services. This is only available
while the cluster, gateway speaker, and LAN are functioning; the single
control-plane node remains a single point of failure.

## Next stage

Install cert-manager, establish and back up a private root CA, distribute its
trust anchor to the laptop and NUC, issue private TLS certificates, and route
sensitive services only after checking authentication and authorization.
Headlamp must retain read-only privileges and must not use an unprotected
service-account-token auto-login.
