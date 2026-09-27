# Prometheus private HTTPS access

The Prometheus Service remains ClusterIP. This pilot puts a Traefik BasicAuth
gate on its LAN-only HTTPS Ingress without changing Prometheus' internal
service, scrape configuration, or Grafana data source. Traefik removes the
Authorization header before sending authenticated requests to Prometheus.
The existing gateway default TLSStore serves the private CA certificate.

The credential is a Kubernetes `kubernetes.io/basic-auth` Secret in
`forge-observability`. Traefik's documented form stores username and
password as plaintext in the Secret (base64 is not encryption). Keep the
password unique and in a password manager; never commit it or print its
Secret. A future identity service can replace this local gate.

## Stage and verify

Use the current laptop checkout and the reviewed kube context. Validate the
resource shapes first, without exposing the route:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --dry-run=server --context $ctx -f .\k8s\lan-portal\prometheus-private-ingress.yaml
```

Create the Secret using a hidden prompt. This passes the Secret JSON through
stdin to kubectl; the password is not placed in process arguments or a
tracked file. Run in a PowerShell session without transcript logging and do
not paste variable contents into chat. Use a distinct strong password from
your password manager.

```powershell
$userName = Read-Host 'Prometheus LAN username'
if ($userName -notmatch '^[A-Za-z0-9._-]+$') { throw 'Use a simple username' }
$securePassword = Read-Host 'Prometheus LAN password' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
  $secretBody = @{
    apiVersion = 'v1'
    kind = 'Secret'
    metadata = @{ name = 'prometheus-lan-auth'; namespace = 'forge-observability' }
    type = 'kubernetes.io/basic-auth'
    stringData = @{
      username = $userName
      password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
  }
  $secretBody | ConvertTo-Json -Depth 5 -Compress |
    kubectl apply -f - --context $ctx
  if ($LASTEXITCODE -ne 0) { throw 'Prometheus auth Secret apply failed' }
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  Remove-Variable secretBody,securePassword -ErrorAction SilentlyContinue
}
kubectl get secret prometheus-lan-auth -n forge-observability `
  -o 'jsonpath={.type}' --context $ctx
```

The last command should print only `kubernetes.io/basic-auth`. Do not get
or paste the Secret body. Now apply the middleware and Ingress:

```powershell
kubectl apply --context $ctx -f .\k8s\lan-portal\prometheus-private-ingress.yaml
kubectl get middleware prometheus-lan-auth -n forge-observability --context $ctx
kubectl get ingress prometheus-lan -n forge-observability --context $ctx
```

Before browsing the endpoint, prove the gateway denies anonymous access. If
the check fails or returns any code other than 401, remove the Ingress
immediately and inspect the middleware; do not add a portal link.

```powershell
$caFile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'forge-root-ca.crt'
$code = curl.exe -sS --ssl-revoke-best-effort --cacert $caFile `
  --resolve prometheus.forge.home.arpa:443:192.168.243.250 `
  -o NUL -w '%{http_code}' `
  'https://prometheus.forge.home.arpa/api/v1/query?query=up'
if ($LASTEXITCODE -ne 0 -or $code -ne '401') {
  kubectl delete ingress prometheus-lan -n forge-observability --context $ctx
  throw "Prometheus gateway did not deny anonymous access: $code"
}
```

Add `192.168.243.250 prometheus.forge.home.arpa` to the laptop hosts file as
Administrator. Open `https://prometheus.forge.home.arpa/` in Edge, enter the
new credential when the browser prompts, and inspect Status > Targets and a
bounded query. No credentials should be shared in chat or used with
`curl --user` on the command line. Live laptop acceptance passed: the anonymous query returned 401; Edge
accepted the login without certificate warnings and displayed Targets and an
`up` query. Reconcile the portal card from the tracked manifest:

```powershell
kubectl apply --context $ctx -f .\k8s\lan-portal\portal.yaml
kubectl rollout restart deployment/forge-portal -n forge-portal --context $ctx
kubectl rollout status deployment/forge-portal -n forge-portal --context $ctx --timeout=120s
```

On the NUC, defer access until its public-root trust and hosts entries are
installed.

Deleting only `ingress/prometheus-lan` removes LAN exposure if a test fails;
the internal Service and Grafana's data source continue to work. Remove the
Middleware and Secret only after the Ingress no longer references them.
