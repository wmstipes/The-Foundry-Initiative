# Grafana private HTTPS access

Grafana already requires its own login: anonymous access and self-registration
are disabled. The existing `grafana-admin` Secret remains in the cluster;
no credential belongs in Git. This change gives Grafana a stable LAN address
and tells it to issue secure session cookies. Traefik uses the private CA
certificate from its default TLSStore. The dashboard stays on its ClusterIP
Service and no new load-balancer address is allocated.

Apply from the repository root in Windows PowerShell after verifying that
the public root CA is trusted on this client and the host name resolves to
the Forge gateway. Add this hosts entry if needed (edit as Administrator):

```text
192.168.243.250 grafana.forge.home.arpa
```

Review the target Ingress before making any changes:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --dry-run=server --context $ctx -f .\k8s\lan-portal\grafana-ingress.yaml
```

Grafana's old `root_url` was `http://127.0.0.1:3000/`. Update only its
configuration ConfigMap from the tracked directory, then restart its single
replica to load the new URL and secure-cookie setting. This causes a brief
Grafana interruption; Prometheus collection remains separate. Do not delete
the Grafana PVC or Secret. Check each command before continuing:

```powershell
kubectl create configmap grafana-config -n forge-observability `
  --from-file=.\k8s\grafana\config --dry-run=client -o yaml --context $ctx |
  kubectl apply -f - --context $ctx

kubectl rollout restart deployment/grafana -n forge-observability --context $ctx
kubectl rollout status deployment/grafana -n forge-observability --context $ctx --timeout=300s
kubectl apply -f .\k8s\lan-portal\grafana-ingress.yaml --context $ctx
```

Confirm the response and anonymous access without disclosing credentials:

```powershell
$caFile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'forge-root-ca.crt'
curl.exe -sS --ssl-revoke-best-effort --cacert $caFile `
  --resolve grafana.forge.home.arpa:443:192.168.243.250 `
  -o NUL -w "Grafana login: %{http_code}`n" `
  https://grafana.forge.home.arpa/login
curl.exe -sS --ssl-revoke-best-effort --cacert $caFile `
  --resolve grafana.forge.home.arpa:443:192.168.243.250 `
  -o NUL -w "Anonymous dashboard API: %{http_code}`n" `
  https://grafana.forge.home.arpa/api/search
```

Open `https://grafana.forge.home.arpa/` in Edge and sign in with the
existing Grafana credentials. Check a dashboard and Loki Explore. Expect
`/login` to load and the unauthenticated dashboard API to deny access.
The historical `open-grafana.ps1` browser flow uses plain HTTP
port-forwarding and is superseded for interactive login by this HTTPS URL;
its health checks can still use the internal Service.

Live laptop acceptance passed: HTTPS login returned 200, anonymous dashboard
search returned 401, and Edge opened the dashboards and Loki Explore without a
certificate warning. The portal card can now be reconciled from the tracked
manifest:

```powershell
kubectl apply -f .\k8s\lan-portal\portal.yaml --context $ctx
kubectl rollout restart deployment/forge-portal -n forge-portal --context $ctx
kubectl rollout status deployment/forge-portal -n forge-portal --context $ctx --timeout=120s
```

NUC access needs its own verified public-root import and hosts entry. If the
Ingress fails, delete only `ingress/grafana` in `forge-observability`;
the ClusterIP Service and existing metrics collection remain available.
