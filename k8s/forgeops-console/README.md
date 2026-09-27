# ForgeOps Console on the cluster (single-operator pilot)

This is a separate runtime mode from the Windows workstation preview. The
existing preview continues to require an explicit kubeconfig and binds to
loopback. The in-cluster mode accepts no kubeconfig: client-go uses only the
Pod's projected ServiceAccount token and the Kubernetes CA. It exposes the
single fixed context `forge`, so workstation EKS contexts are unavailable.
The Console has one process-wide scope and session nonce. Use **one operator
at a time**; simultaneous browser sessions can change each other's scope.

The Pod is one restricted, stateless ARM64 replica with a ClusterIP Service.
A NetworkPolicy permits ingress only from the Traefik pods in
`forge-gateway`. Traefik terminates private HTTPS at the existing gateway
TLSStore and requires a distinct BasicAuth Secret in `forge-console`.
The ServiceAccount can list/get Namespaces, Nodes, Pods, Deployments,
ReplicaSets, Services, EndpointSlices and Events, and read Pod logs across
namespaces. It cannot read Secrets or modify objects. Logs and Events can
contain sensitive values and are not automatically redacted. BasicAuth is a
single-user LAN gate, not Kubernetes user identity or per-user RBAC.

## Build and release

The image workflow validates an AMD64/ARM64 build in the PR. After the code
PR is reviewed and merged to main, run the **ForgeOps Console cluster image**
workflow on `main` with version `0.1.0`. Its publish job requires the
release environment and existing Docker Hub credentials. Read the OCI index
digest from the run summary. Confirm both platforms and image name before
installing. The manifest deliberately has an invalid digest placeholder:
do not apply the Deployment until the real digest is reviewed.

## Stage a private deployment

Run from the repository root on the laptop. Apply the Namespace and Role
first. Check the binding's effective authorization: it must permit the
named read operations and deny Secret reads and writes.

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --context $ctx -f .\k8s\forgeops-console\namespace.yaml
kubectl apply --dry-run=server --context $ctx -f .\k8s\forgeops-console\rbac.yaml
kubectl apply --context $ctx -f .\k8s\forgeops-console\rbac.yaml
$sa = 'system:serviceaccount:forge-console:forgeops-console'
kubectl auth can-i list nodes --as $sa --context $ctx
kubectl auth can-i get pods/log -n forge-restaurant --as $sa --context $ctx
kubectl auth can-i get secrets -n forge-restaurant --as $sa --context $ctx
kubectl auth can-i create deployments -n forge-restaurant --as $sa --context $ctx
```

The answers must be `yes`, `yes`, `no`, `no`. NetworkPolicy enforcement
depends on Calico; verify its ingress behavior before exposing the route.

Paste the reviewed digest from the release job summary into `$digest`. The
placeholder substitution is in memory; it does not change the tracked file.
The dry run must succeed before applying:

```powershell
$digest = 'sha256:PASTE_REVIEWED_64_HEX_DIGEST'
if ($digest -notmatch '^sha256:[0-9a-f]{64}$') { throw 'Invalid digest' }
$manifest = (Get-Content -Raw .\k8s\forgeops-console\deployment.yaml).
  Replace('sha256:REPLACE_WITH_RELEASE_DIGEST', $digest)
$manifest | kubectl apply --dry-run=server -f - --context $ctx
if ($LASTEXITCODE -ne 0) { throw 'Deployment validation failed' }
kubectl apply --context $ctx -f .\k8s\forgeops-console\network-policy.yaml
$manifest | kubectl apply -f - --context $ctx
if ($LASTEXITCODE -ne 0) { throw 'Deployment apply failed' }
kubectl rollout status deployment/forgeops-console -n forge-console --context $ctx --timeout=300s
kubectl get pods,service,networkpolicy -n forge-console --context $ctx
Remove-Variable manifest
```

The Console must remain private until the auth gate is tested. Create a
**new**, strong credential in the password manager. Traefik's BasicAuth
Secret stores it as plaintext (base64 is not encryption). Do not commit,
paste, or print the Secret or password. Use PowerShell without transcript
logging:

```powershell
$userName = Read-Host 'ForgeOps Console LAN username'
if ($userName -notmatch '^[A-Za-z0-9._-]+$') { throw 'Use a simple username' }
$securePassword = Read-Host 'ForgeOps Console LAN password' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
  $secretBody = @{
    apiVersion = 'v1'
    kind = 'Secret'
    metadata = @{ name = 'forgeops-console-auth'; namespace = 'forge-console' }
    type = 'kubernetes.io/basic-auth'
    stringData = @{
      username = $userName
      password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
  }
  $secretBody | ConvertTo-Json -Depth 5 -Compress |
    kubectl apply -f - --context $ctx
  if ($LASTEXITCODE -ne 0) { throw 'Console auth Secret apply failed' }
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  Remove-Variable secretBody,securePassword -ErrorAction SilentlyContinue
}
kubectl get secret forgeops-console-auth -n forge-console -o 'jsonpath={.type}' --context $ctx
```

The last command should print `kubernetes.io/basic-auth`. Now apply the
Ingress and immediately test anonymous denial with CA and hostname
verification. Remove the Ingress if the response is not exactly 401:

```powershell
kubectl apply --dry-run=server --context $ctx -f .\k8s\forgeops-console\ingress.yaml
kubectl apply --context $ctx -f .\k8s\forgeops-console\ingress.yaml
$caFile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'forge-root-ca.crt'
$code = curl.exe -sS --ssl-revoke-best-effort --cacert $caFile `
  --resolve forgeops.forge.home.arpa:443:192.168.243.250 `
  -o NUL -w '%{http_code}' `
  https://forgeops.forge.home.arpa/api/v1/bootstrap
if ($LASTEXITCODE -ne 0 -or $code -ne '401') {
  kubectl delete ingress forgeops-console -n forge-console --context $ctx
  throw "Anonymous Console request was not denied: $code"
}
```

Add `192.168.243.250 forgeops.forge.home.arpa` to the laptop hosts file
as Administrator. Open `https://forgeops.forge.home.arpa/` in Edge.
After signing in, select `forge` and a namespace. Confirm bounded
resource lists, a Pod log after acknowledging the warning, and no
certificate error. Keep NUC setup deferred until its hosts and public-root
trust are in place. After live acceptance, update the Forge home page card
to the verified URL and label it as protected.

Rollback: delete `ingress/forgeops-console` in `forge-console` to remove
LAN exposure. The Windows preview and other cluster Services are unaffected.
