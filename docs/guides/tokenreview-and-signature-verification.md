# How to diagnose OIDC tokens with TokenReview and signature verification

**Audience:** the Forge operator using Windows PowerShell, kubectl and Edge.
**Reviewed:** 2026-09-30. Examples use the existing private Dex issuer and Headlamp
client; they do not install tools or change cluster authentication configuration.

## 1. Why use two checks?

Dex issues a signed ID token after login. Headlamp uses it to access Kubernetes
on the user's behalf. A successful Dex login does not prove Kubernetes accepts
that token, and a successful Kubernetes login does not grant every permission.

| Check | Question answered | What it does not establish |
| --- | --- | --- |
| Decode JWT header/claims | What key ID, algorithm, issuer, audience and times does this token claim? | Authenticity: anyone can construct a header or payload |
| Local signature verification | Does this exact token match the trusted published public key mathematically? | Expiry, expected issuer/audience, API-server acceptance or RBAC permissions |
| Kubernetes TokenReview | Does this API server authenticate this token, and as which user? | Whether that user may list Pods, read Secrets or perform another action |
| Actual user request / RBAC check | Is this identity authorized for the requested operation? | An impersonation-only check does not validate the user's real token |

A JWT has three base64url parts separated by periods: **header.payload.signature**.
The signature covers the exact encoded header and payload; reformatting or changing
one byte invalidates it. RS256 is RSA with SHA-256 and PKCS#1 v1.5 signature padding.
The public key verifies signatures; no Dex private signing key is needed.

In our September 30 incident, local verification was true while TokenReview was
false. After an approved API-server restart, the same token passed TokenReview.
That isolated the failure to the API-server verification path/state rather than
an inherently invalid signature, without proving the exact internal mechanism.
See the [incident record](../incidents/2026-09-30-headlamp-oidc-signature-rejection.md).

## 2. When to use it and prepare

Use TokenReview when login/consent completes but Kubernetes rejects the session,
or when you need to separate Headlamp/gateway failures from API authentication.
Use local verification when the error specifically concerns a signature or key.
Neither is the first check for DNS/TLS failures, unavailable Pods, a rejected
BasicAuth password, or an authenticated user receiving a permissions error.

Before starting:

1. Confirm the administrator context is `kubernetes-admin@kubernetes` and the API
   is ready. This administrator credential submits the diagnostic request; the
   token in `spec.token` is the different credential being evaluated.
2. Use a current token from the affected browser session, not a Kubernetes
   ServiceAccount token or the Dex refresh/access token. These examples assume
   Headlamp uses its ID token and `RS256`.
3. Keep the full token private. Paste only into the hidden local prompt. Avoid
   shell history, command-line arguments, HAR exports, screenshots, online token
   decoders and chat. Nulling variables is best-effort cleanup, not guaranteed
   memory erasure; logout is not revocation of an already issued JWT.
4. Confirm the issuer HTTPS certificate is trusted. Never accept a key URL taken
   from an unverified token. The scripts fetch only the configured Forge issuer.
5. If changing configuration later, capture evidence and backups first; these
   diagnostic results alone do not authorize a restart or RBAC expansion.

```powershell
kubectl --context kubernetes-admin@kubernetes get --raw='/readyz' --request-timeout=5s
kubectl --context kubernetes-admin@kubernetes auth can-i create tokenreviews.authentication.k8s.io
```

Expect `ok` and `yes`. A request-level Forbidden means the submitting identity
cannot run TokenReview; it is not evidence that the examined token is invalid.
Do not grant TokenReview permission to normal users merely to troubleshoot.

In Edge, press F12, open **Application → Storage → Cookies**, and select the
Headlamp HTTPS origin. Headlamp 0.45.0 uses `headlamp-auth-main.0` and may use
additional numbered chunks. Copy only locally. If the cookie is absent after
rejection, use the capture note below; an empty cookie table is not evidence
that Dex failed to issue a token.

## 3. Run TokenReview

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

## 4. Verify the signature locally

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

## 5. Read the results

| TokenReview | Local signature | Interpretation and next step |
| --- | --- | --- |
| Authenticated=true, ExpectedUser=true | Not needed unless investigating a specific anomaly | API authentication works. Check Headlamp session, gateway challenge and requested-operation RBAC if the UI still fails. |
| Authenticated=true, ExpectedUser=false | Any | Token accepted under another identity. Compare configured username claim/prefix and the intended account privately; do not add privileges to make the test pass. |
| Authenticated=false, SignatureError=true | True | Verify the same complete token was used, then compare trusted keys and the API process's issuer/CA/resolution path. Preserve evidence before considering the conditional restart runbook. |
| Authenticated=false, SignatureError=true | False | Recopy the complete token without modification. Check all cookie chunks, signing-key rotation and that the published key belongs to the intended issuer. Do not assume an API cache problem. |
| Authenticated=false, ErrorPresent=true, SignatureError=false | True or unknown | Inspect the private error for expiry, issuer/audience mismatch, discovery, TLS or network failure. A valid signature does not override these checks. |
| Authenticated=false, ErrorPresent=false | Any | No identity was established; absence of error text is not success. Correlate bounded API logs and token type. |
| Request command fails | Not applicable | Diagnose kubectl/context, connectivity, request format or submitting-user permissions first. |
| Matching key missing | Cannot verify | Check rotation, wrong issuer, old/recovered session or incomplete token; never substitute an arbitrary key. |

`SignatureError` is a convenience phrase match, not a complete error taxonomy.
Keep raw TokenReview responses private: they can echo the submitted token.
`ExpectedUser` is specific to Forge's current `forge:operator@forge.home.arpa`
identity; change the expectation only for a deliberately different user.

### What to inspect in a token, privately

| Field | Expected meaning / Forge check |
| --- | --- |
| Header `alg` | `RS256`; unsupported algorithms stop this verifier |
| Header `kid` | Selects a public key; also compare RSA modulus `n` and exponent `e` |
| Payload `iss` | Exactly `https://auth.forge.home.arpa` |
| Payload `aud` | Includes the configured OIDC client `headlamp`; may be a string or array |
| Payload `exp` | Expiration as Unix seconds; compare with current UTC clock |
| Payload `iat`, optional `nbf` | Issued/not-before times; investigate clock skew or future validity |
| Payload `email`, `email_verified` | Intended user claim and verification state; avoid publishing personal claims |

These claims remain untrusted until verification succeeds. Even after local
signature verification, Kubernetes must apply its configured claim/audience/time
rules. BasicAuth username and Kubernetes OIDC username need not be identical.

### Rotation and restored providers

A provider can publish an active signing key plus old verification keys. Independent
original and restored Dex instances may generate different new keys after a backup.
Different whole JWKS sets can therefore be expected; compare the token's particular
key and shared public material. A key's presence does not prove a token is unexpired.
A backup cannot contain signing keys generated after it was captured.

## 6. What to record and what to do next

Record timestamp/timezone, relevant versions, issuer, public `kid`, the four
TokenReview booleans, local SignatureValid, and pre/post-change results for the
same token. Do not store the token, cookies, private JWK or full response in Git.
Use the [incident template](../incidents/TEMPLATE.md). TokenReview is not a fix;
local verification is not a workaround that disables Kubernetes authentication.

If the same signature-valid token is rejected by Kubernetes, follow the
[OIDC troubleshooting runbook](../runbooks/headlamp-oidc-troubleshooting.md)
for host-side checks and the conditional, explicitly authorized API restart.
Do not repeat restarts when evidence points to another cause. Finish with a fresh
browser login, resource navigation and refresh; count initial BasicAuth prompts
separately from recurring challenges.

References: [Kubernetes TokenReview](https://kubernetes.io/docs/reference/kubernetes-api/definitions/token-review-v1-authentication/),
[.NET RSA verification](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.rsa.verifydata).
The local cryptographic test checks signatures only; it is not a replacement for
an OIDC verifier or a general-purpose JWT validation library.
