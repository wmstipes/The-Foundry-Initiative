# Headlamp and Service Pulse protected routes

Both routes were activated on 2026-09-28 and are linked from the running
portal. This is the route procedure; app rollout, Dex configuration, and
API-server authentication have separate lifecycles.

| Application | Namespace | Backend Service and port | Ingress | BasicAuth Secret |
| --- | --- | --- | --- | --- |
| Headlamp | `forge-headlamp` | `headlamp:80` | `headlamp-private` | `headlamp-lan-auth` |
| Pulse board | `forge-pulse` | `service-pulse-board:8080` | `service-pulse-private` | `service-pulse-lan-auth` |

The corresponding `private-ingress.yaml` in each application directory
contains both its Middleware and Ingress. Its `network-policy.yaml` admits
the application's Pod port from Traefik's namespace and Pod labels. Headlamp
uses target port 4466 and Pulse uses 8080. The policy does not grant broader
network isolation to the Pulse probe, and an ingress-only policy does not
restrict egress. Applied policy structure and working gateway access are
recorded; a deliberate bypass/enforcement test has not been recorded.

## Preconditions before a route change

Verify the intended context, Ready workload, Service selectors and endpoints,
Traefik labels, hostname resolution, and Ready gateway certificate. Provision
each credential Secret privately before the Middleware, using the existing
`kubernetes.io/basic-auth` type with its required username and password keys.
Do not print its data or put credentials in Git or command arguments.

For each application, inspect the existing policy and route. Run server
dry-run and diff on the named `network-policy.yaml` and `private-ingress.yaml`.
An approved new route is applied in that order: policy first, then
Middleware/Ingress. Check each command's exit status before continuing.
The gateway uses its existing TLSStore certificate and HTTPS redirection;
the absence of a per-Ingress TLS Secret is not evidence that client HTTPS
is disabled. Actual certificate validation is part of acceptance.

## Anonymous HTTPS verification

Run from the Windows client with its public CA file present and the expected
hostnames resolving to the gateway. This is a read-only check:

```powershell
$caFile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'forge-root-ca.crt'
if (-not (Test-Path -LiteralPath $caFile)) { throw 'Public CA file missing' }
foreach ($url in @(
  'https://headlamp.forge.home.arpa/',
  'https://pulse.forge.home.arpa/api/status'
)) {
  $code = curl.exe -sS --ssl-revoke-best-effort --cacert $caFile `
    --connect-timeout 5 --max-time 15 -o NUL -w '%{http_code}' $url
  if ($LASTEXITCODE -ne 0 -or $code -ne '401') {
    throw "Anonymous HTTPS check failed for ${url}: $code"
  }
  Write-Host "Anonymous HTTPS gate passed: $url"
}
```

Then use a fresh browser session: verify a BasicAuth prompt for each service,
the Pulse board and fresh samples, and Headlamp's Dex sign-in and expected
read-only access. A `401` alone does not test the backend or OIDC. A cached
browser token does not establish that a fresh sign-in works.

## Close a route without removing the application

After selecting the affected route from the table, remove only that Ingress
using `kubectl delete ingress <name> --namespace <namespace> --context $ctx`.
Keep its workload, policy, and credentials for diagnosis. An inactive portal
card or removed link does not revoke access to an existing route. Conversely,
removing Headlamp's ingress does not disable API-server OIDC or revoke an
already issued Kubernetes token. Application and identity revocation require
their own reviewed steps.

Use the [Headlamp runbook](../headlamp/README.md),
[identity operations](../../docs/runbooks/headlamp-oidc.md), and
[Pulse workload runbook](../service-pulse/README.md) for those components.
