# Headlamp cluster viewer

This is the read-only Headlamp 0.45.0 pilot in `forge-headlamp`. The Helm
release is named `headlamp`. The Service remains ClusterIP; the UI is linked
from the LAN portal through a protected HTTPS ingress. The namespace
enforces the Kubernetes v1.36 restricted Pod Security profile. The pod requests
50m CPU and 128Mi memory and is capped at 300m CPU and 512Mi memory.

## Running configuration and recovery boundary

Headlamp revision 2 uses the tracked base values **and a private OIDC values
overlay outside Git**. Its OIDC client credentials and the public CA mount
come from Kubernetes Secrets created separately. The API server validates
Dex-issued tokens and binds the Forge operator identity to built-in `view` and
a scoped Node reader. The existing ingress BasicAuth prompt remains active.
Never run an upgrade using only the base values: it would remove the OIDC
settings from Headlamp. Keep the private overlay, Dex configuration, public
CA, and control-plane recovery copies available to the operator. The public
repository does not contain everything needed to recreate this installation.

From the repository root in PowerShell, inspect the deployed revision and
verify the private overlay is present before a later upgrade:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
helm history headlamp --namespace forge-headlamp --kube-context $ctx
$overlayPath = Join-Path (Join-Path $env:USERPROFILE 'Forge-Private-OIDC') 'headlamp-oidc-values.yaml'
if (-not (Test-Path -LiteralPath $overlayPath)) { throw 'Private OIDC overlay missing; stop' }
```

The original local token workflow below is a possible recovery option, not
the normal sign-in procedure; it has not been retested since OIDC was enabled.
Dex and the gateway must be available for new OIDC logins. See
[identity architecture](../../docs/architecture.md#headlamp-identity-and-authorization).
For troubleshooting and recovery inputs, see [identity operations](../../docs/runbooks/headlamp-oidc.md).
The [protected route runbook](../lan-portal/protected-apps.md) owns ingress
checks and route removal.

## Reconcile the current release

From the repository root in PowerShell, with Helm installed and the Headlamp
chart repository added (`helm repo add headlamp
https://kubernetes-sigs.github.io/headlamp/`):

```powershell
$ctx = 'kubernetes-admin@kubernetes'
$overlayPath = Join-Path (Join-Path $env:USERPROFILE 'Forge-Private-OIDC') 'headlamp-oidc-values.yaml'
if (-not (Test-Path -LiteralPath $overlayPath)) { throw 'Private OIDC overlay missing; stop' }
kubectl apply -f .\k8s\headlamp\namespace.yaml --context $ctx
if ($LASTEXITCODE -ne 0) { throw 'Namespace reconciliation failed' }
kubectl get secret forge-headlamp-oidc forge-headlamp-ca `
  -n forge-headlamp --context $ctx -o name
if ($LASTEXITCODE -ne 0) { throw 'OIDC secrets missing; stop' }
helm upgrade --install headlamp headlamp/headlamp `
  --version 0.45.0 --namespace forge-headlamp --kube-context $ctx `
  --values .\k8s\headlamp\values.yaml `
  --values $overlayPath `
  --wait --timeout 5m --rollback-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Headlamp upgrade failed; inspect release history' }
kubectl apply -f .\k8s\headlamp\node-reader.yaml --context $ctx
```

Do not run Helm with only the tracked base values against this installation.
For a later upgrade, review the rendered diff and retain rollback on failure.

The Helm chart creates the ServiceAccount and a ClusterRoleBinding whose
`roleRef.name` must be `view`. The chart names that binding `headlamp-admin`
even though it grants `view`; check `roleRef`, not the object name. The separate
`node-reader.yaml` provides only `get/list/watch` on Nodes because the
Kubernetes built-in `view` role does not grant node listing in this cluster.
The existing Metrics Server and `view` role supply read access to pod and node
resource metrics. Never install the chart with its default `cluster-admin`
binding, and keep `config.unsafeUseServiceAccountToken` false.

## Verify access and authorization

```powershell
$sa = 'system:serviceaccount:forge-headlamp:headlamp'
kubectl get deployment,pods,service -n forge-headlamp --context $ctx
kubectl auth can-i list nodes --as $sa --context $ctx
kubectl auth can-i list pods --all-namespaces --as $sa --context $ctx
kubectl auth can-i get secrets --all-namespaces --as $sa --context $ctx
kubectl auth can-i create deployments -n forge-restaurant --as $sa --context $ctx
```

The four ServiceAccount authorization answers should be `yes`, `yes`, `no`,
`no`. The OIDC user has separate `view` and Node-reader bindings with the
same observed allow/deny pattern. In the browser, open the Headlamp card,
complete the existing BasicAuth prompt, select **Sign in**, and authenticate
with the private Dex account. On 2026-09-28 the API server returned `ok`, the
Headlamp deployment rolled out, and the operator reported successful OIDC
login and cluster browsing. If testing the earlier local access path for
recovery, port-forward the Service and issue a short-lived ServiceAccount
token without printing it:

```powershell
kubectl port-forward service/headlamp 8080:80 `
  --namespace forge-headlamp --context $ctx
# In a second PowerShell window:
kubectl create token headlamp --namespace forge-headlamp `
  --context kubernetes-admin@kubernetes --duration=1h | Set-Clipboard
```

Visit `http://127.0.0.1:8080` and paste the token into the login screen.
Do not commit or share the token. Clear the clipboard after use. The original
token-based pilot displayed four Ready nodes,
workloads, CPU/memory usage, and an initial Headlamp readiness-probe Event.
That single startup Event was observed while the pod subsequently became
Ready; the pilot does not establish long-term uptime or log persistence.

## Uninstall (separate approved operation)

```powershell
helm uninstall headlamp --namespace forge-headlamp --kube-context $ctx
kubectl delete -f .\k8s\headlamp\node-reader.yaml --context $ctx
```

The uninstall command also removes the running OIDC-enabled Headlamp release;
it is not an OIDC rollback procedure. Keep the namespace for review or remove
it separately after checking it contains no other resources. The ingress,
Dex deployment, Secrets, and API-server OIDC settings have separate lifecycles.
