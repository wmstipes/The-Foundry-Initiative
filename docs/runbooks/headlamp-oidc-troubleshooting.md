# Headlamp OIDC signature troubleshooting

Use for Dex login followed by cluster rejection or repeated gateway challenges.
The [September 30 incident](../incidents/2026-09-30-headlamp-oidc-signature-rejection.md)
records the observed recovery; a similar symptom does not prove the same cause.

Prerequisites: authorized administrator context, trusted issuer HTTPS, private
local evidence directory, SSH fallback and current recovery backups before a
control-plane interruption. Run PowerShell blocks on Windows; Linux blocks only
inside SSH to `forge-head`. Keep private exports, logs and tokens outside Git.

## 1. Distinguish the authentication layers

Browser-native BasicAuth, Dex login/consent, Headlamp callback, API authentication
and Kubernetes RBAC are separate checks. Inspect request **path, status and
WWW-Authenticate scheme/realm** without copying request headers, cookie values or
callback query strings. A console JSON parsing error may be a non-JSON HTTP error;
it does not prove issuer misconfiguration. A 403 after successful authentication
calls for RBAC investigation, not a signing-key restart.

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl --context $ctx get --raw='/readyz' --request-timeout=5s
kubectl --context $ctx get pods -A
kubectl --context $ctx -n forge-identity get deployments,services,ingresses,networkpolicies
kubectl --context $ctx -n forge-headlamp get deployments,ingresses
```

For a gateway-only check, the following prompts for the BasicAuth password without
putting it into shell history. HTTP 200 proves this request passed, not OIDC login.
Use `--ssl-revoke-best-effort` only for the known Windows/private-PKI revocation
availability issue; it does not disable hostname or CA verification. Do not use `-k`.

```powershell
$gatewayUser = Read-Host 'Gateway BasicAuth username'
curl.exe --basic --user $gatewayUser --ssl-revoke-best-effort `
    --fail --silent --show-error --connect-timeout 10 --max-time 20 `
    --output NUL --write-out 'HTTP status: %{http_code}\n' `
    'https://headlamp.forge.home.arpa/config'
```

## 2. Preserve bounded logs privately

Use an already protected directory. Do not paste raw logs into an issue or chat.
Capture before a restart; use `--previous` separately if a container already
restarted. Previous logs may be absent or rotated; absence is not a clean bill of health.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $privateLogs = Read-Host 'Existing protected directory for diagnostic logs'
    if (-not (Test-Path -LiteralPath $privateLogs -PathType Container)) {
        throw 'Protected directory must already exist'
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $apiLog = Join-Path $privateLogs "apiserver-$stamp.log"
    kubectl --context kubernetes-admin@kubernetes -n kube-system `
        logs kube-apiserver-forge-head -c kube-apiserver --timestamps --since=10m --tail=1000 `
        2>&1 | Set-Content -LiteralPath $apiLog
    if ($LASTEXITCODE -ne 0) { throw 'API log capture failed; inspect locally' }
    [pscustomobject]@{
        SignatureErrorLines = @(Select-String -LiteralPath $apiLog `
            -SimpleMatch 'failed to verify id token signature').Count
    }
}
```

Repeat scoped capture for `-n forge-headlamp logs deployment/headlamp` and
`-n forge-identity logs deployment/forge-dex` into separate private files if needed.
The [logging plan](identity-logging-plan.md) describes collection gaps and future
LogQL queries; these identity logs are not part of the accepted Pulse-only pipeline.

## 3. Check token authentication directly

Obtain the current cookie token locally in browser developer tools. Headlamp can
clear cookies after rejection; if necessary, disable JavaScript on the Dex consent
page before granting access and inspect the resulting Headlamp cookie before the
frontend runs. Re-enable JavaScript afterward. Cookie chunks, if present, must be
assembled in numeric order; do not treat a partial cookie as a complete JWT.
Never paste a full token into chat, an issue, a shell command line, or a screenshot.
Do not use an online JWT decoder. A decoded key ID is not signature verification.

This sends the token only to the configured Kubernetes API via administrator
credentials. TokenReview is an authentication check, not a persistent workload
change or an RBAC check. Keep request/response bodies private; review any audit
policy before capturing TokenReview bodies centrally.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $secureToken = Read-Host 'Cookie token (hidden; local only)' -AsSecureString
    try {
        $token = [System.Net.NetworkCredential]::new('', $secureToken).Password.Trim()
        $request = @{
            apiVersion = 'authentication.k8s.io/v1'
            kind = 'TokenReview'
            spec = @{ token = $token }
        } | ConvertTo-Json -Depth 5 -Compress
        $raw = $request | kubectl --context kubernetes-admin@kubernetes create `
            --raw='/apis/authentication.k8s.io/v1/tokenreviews' -f - 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'TokenReview request failed; do not print raw bodies' }
        $review = ($raw -join "`n") | ConvertFrom-Json
        [pscustomobject]@{
            Authenticated = ($review.status.authenticated -eq $true)
            ExpectedUser = ($review.status.user.username -eq 'forge:operator@forge.home.arpa')
            SignatureError = ([string]$review.status.error -match 'failed to verify.*signature')
            ErrorPresent = -not [string]::IsNullOrWhiteSpace($review.status.error)
        }
    }
    finally {
        $token = $request = $raw = $review = $null
        $secureToken.Dispose()
    }
}
```

If authenticated, investigate the browser/gateway/Headlamp flow or RBAC as indicated;
do not restart the API server. If rejected, classify the private error before
changing configuration. This incident's error was cryptographic signature failure.

## 4. Verify an RS256 signature against published keys locally

Use the same complete token as TokenReview. This verifies the signature only;
it does not check expiry, issuer, audience or authorization. The known trusted
issuer URL is fixed below; do not follow a URL from an unverified token.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    function Decode-Base64Url([string]$Value) {
        $encoded = $Value.Replace('-', '+').Replace('_', '/')
        $encoded += '=' * ((4 - ($encoded.Length % 4)) % 4)
        return ,([Convert]::FromBase64String($encoded))
    }
    $rawKeys = curl.exe --ssl-revoke-best-effort --fail --silent --show-error `
        --connect-timeout 10 --max-time 20 'https://auth.forge.home.arpa/keys'
    if ($LASTEXITCODE -ne 0) { throw 'Trusted public-key fetch failed' }
    $keys = ($rawKeys -join "`n") | ConvertFrom-Json
    $secureToken = Read-Host 'Same complete cookie token (hidden)' -AsSecureString
    $rsa = $null
    try {
        $token = [System.Net.NetworkCredential]::new('', $secureToken).Password.Trim()
        $parts = $token.Split('.')
        if ($parts.Count -ne 3) { throw 'Expected complete JWT' }
        $header = [Text.Encoding]::UTF8.GetString((Decode-Base64Url $parts[0])) | ConvertFrom-Json
        if ($header.alg -cne 'RS256') { throw 'Unexpected algorithm' }
        $matches = @($keys.keys | Where-Object { $_.kid -ceq $header.kid })
        if ($matches.Count -ne 1 -or $matches[0].kty -cne 'RSA') {
            throw 'Expected one matching RSA public key'
        }
        $parameters = [System.Security.Cryptography.RSAParameters]::new()
        $parameters.Modulus = Decode-Base64Url $matches[0].n
        $parameters.Exponent = Decode-Base64Url $matches[0].e
        $rsa = [System.Security.Cryptography.RSA]::Create()
        $rsa.ImportParameters($parameters)
        $signed = [Text.Encoding]::ASCII.GetBytes($parts[0] + '.' + $parts[1])
        $signature = Decode-Base64Url $parts[2]
        [pscustomobject]@{
            KeyID = $header.kid
            SignatureValid = $rsa.VerifyData($signed, $signature,
                [System.Security.Cryptography.HashAlgorithmName]::SHA256,
                [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)
        }
    }
    finally {
        if ($null -ne $rsa) { $rsa.Dispose() }
        $secureToken.Dispose()
        $token = $parts = $signed = $signature = $null
    }
}
```

For this incident, host-side public-key retrieval also succeeded with the expected
CA and gateway address. Run from PowerShell and inspect only public material:

```powershell
ssh wmstipes@forge-head 'curl --noproxy auth.forge.home.arpa --fail --silent --show-error --connect-timeout 5 --max-time 15 --cacert /etc/ssl/certs/ca-certificates.crt --resolve auth.forge.home.arpa:443:192.168.243.250 https://auth.forge.home.arpa/keys'
```

Compare RSA `n`, `e`, `kty` as well as `kid`; matching IDs alone are insufficient.
This host check does not inspect the API process's in-memory keys. Avoid wildcard
`--noproxy '*'` across PowerShell/SSH quoting; a lost quote previously expanded
remote filenames into curl arguments. Verify issuer discovery's `jwks_uri` when
checking a different configuration rather than assuming `/keys`.

## 5. Controlled API-server restart: conditional, interrupting procedure

Use only after reviewing valid-token rejection, current issuer/key reachability,
live authentication arguments and hostname mapping, and preserving evidence.
Obtain explicit authorization for the single-control-plane interruption. Verify
SSH/admin fallback, current backups and readiness first. Do not edit keys, weaken
signature validation, or restart multiple components to make an error disappear.

The September 30 baseline below is historical. For another incident, independently
review the current manifest and set its expected SHA-256; do not simply replace
a failed hash with a newly observed value to bypass the check. `crictl` was absent
on this host; the reviewed fallback used the installed `ctr` binary.

In an interactive Linux SSH session on `forge-head`:

```bash
sudo python3 - <<'PYTHON'
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ctr = shutil.which("ctr")
if not ctr:
    raise SystemExit("STOP: ctr unavailable; nothing changed")
manifest = Path("/etc/kubernetes/manifests/kube-apiserver.yaml")
expected = "b74502957d83a7d3f67f51b1e351d4c000e8922a2ded34bf957b87d3821a34d2"
if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
    raise SystemExit("STOP: manifest differs from reviewed baseline")
base = [ctr, "--address", "/run/containerd/containerd.sock", "--namespace", "k8s.io"]
def read(*args):
    return subprocess.run(base + list(args), check=True, capture_output=True,
                          text=True, timeout=20).stdout
matches = []
for line in read("tasks", "list").splitlines():
    fields = line.split()
    if len(fields) != 3 or fields[2] != "RUNNING":
        continue
    info = json.loads(read("containers", "info", fields[0]))
    labels = info.get("Labels", {})
    if (labels.get("io.kubernetes.container.name") == "kube-apiserver"
        and labels.get("io.kubernetes.pod.namespace") == "kube-system"
        and labels.get("io.kubernetes.pod.name") == "kube-apiserver-forge-head"):
        matches.append(fields[0])
if len(matches) != 1:
    raise SystemExit("STOP: expected exactly one running API-server container")
print("Sending SIGTERM once to:", matches[0], flush=True)
subprocess.run(base + ["tasks", "kill", "--signal", "SIGTERM", matches[0]],
               check=True, timeout=20)
if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
    raise SystemExit("STOP: manifest changed")
print("PASS: signal sent once; manifest unchanged; verify recovery separately")
PYTHON
```

On failure, do not repeat the mutation automatically. If readiness fails to return,
use SSH to inspect `sudo ctr --namespace k8s.io tasks list` and privately inspect
`sudo journalctl -u kubelet --since '10 minutes ago'`. Keep the existing manifest;
this operation made no configuration change to roll back. Do not stop etcd or
containerd, delete the mirror Pod as a restart substitute, or restore a database.

## 6. Acceptance

Return to PowerShell; a bounded readiness loop is followed by explicit checks:

```powershell
& {
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        $response = kubectl --context kubernetes-admin@kubernetes `
            --request-timeout=3s get --raw='/readyz' 2>$null
        if ($LASTEXITCODE -eq 0 -and ($response -join '').Trim() -eq 'ok') {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'Readiness did not recover; use SSH diagnosis' }
    kubectl --context kubernetes-admin@kubernetes get pods -A
}
```

Repeat TokenReview with the **same still-valid token** for causal comparison.
If expired, a fresh-token test is useful but not equivalent before/after evidence.
Record container replacement/restarts, controller side effects and recovery.
Then perform fresh browser login, resource navigation and refresh with JavaScript
enabled. Record initial and recurring BasicAuth challenges separately. Never
claim root cause solely because a restart helped. Record the result using the
[incident template](../incidents/TEMPLATE.md).

References: [TokenReview](https://kubernetes.io/docs/reference/kubernetes-api/definitions/token-review-v1-authentication/),
[RSA VerifyData](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.rsa.verifydata),
[containerd 1.7.24 task signal implementation](https://github.com/containerd/containerd/blob/v1.7.24/cmd/ctr/commands/tasks/kill.go).
