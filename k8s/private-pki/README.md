# Forge private CA: staged bootstrap

The cluster runs cert-manager v1.21.2 (Helm release `cert-manager`, namespace
`cert-manager`, CRDs managed with `crds.enabled=true`). Bootstrap is separate
from publishing the CA as an issuer. No root key or issued Secret belongs in Git.

1. Confirm encrypted backup tooling and destinations on Windows 11 laptop and
   NUC. Retain another copy on USB. Keep the archive passphrase in a password
   manager, separate from the archive.
2. Apply `root-bootstrap.yaml` to generate the ECDSA root certificate and its
   private key in the `cert-manager/forge-root-ca` Secret.
3. Export that Secret to a **temporary** UTF-8 file on the laptop. In the
   7-Zip GUI, create a `.7z` archive with a strong passphrase, 7z format,
   AES-256 encryption and encrypted filenames. Test the archive by entering
   its passphrase, confirm it contains the expected Secret JSON, and delete the
   plaintext export. Copy the encrypted archive to the NUC and USB; compare
   SHA-256 hashes. Keep the key and passphrase out of the repository and chat.
   Store the public `tls.crt` PEM separately for client trust.
4. Apply `gateway-ca-bootstrap.yaml` to create a temporary root-signing
   ClusterIssuer and a gateway intermediate CA. Wait for the intermediate
   Certificate to become Ready; verify it has a Secret in `forge-gateway`.
5. Apply `gateway-leaf.yaml` to sign the gateway TLS certificate using a
   namespaced Issuer. Wait for its Certificate to become Ready.
6. Remove the temporary ClusterIssuer, then delete the root Certificate,
   root Secret, and bootstrap Issuer, in that order. The intermediate continues
   to issue 90-day gateway leaf certificates. The root's **only** remaining
   private-key copies are the encrypted backups. Do not reapply the stage 1
   bootstrap file during normal operations: it would generate a new root.
7. Monitor intermediate expiry: before its two-year certificate reaches its
   30-day renewal window, securely restore the same root key/certificate,
   temporarily recreate the root-signing ClusterIssuer, renew the intermediate,
   then take the root offline again. Rotating the root trust anchor requires
   its own planned rollout to Windows clients.

Apply stage 1 from the repo root:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply --dry-run=server --context $ctx -f .\k8s\private-pki\root-bootstrap.yaml
kubectl apply --context $ctx -f .\k8s\private-pki\root-bootstrap.yaml
kubectl wait --context $ctx -n cert-manager --for=condition=Ready certificate/forge-root-ca --timeout=120s
kubectl get issuer,certificate -n cert-manager --context $ctx
```

Before stage 2, run `kubectl auth can-i list secrets -n cert-manager --as
system:serviceaccount:forge-gateway:traefik`: the current Traefik chart grants
cluster-wide Secret access (confirmed live). Removing the root Secret after
intermediate issuance limits the impact of a future gateway compromise.
Restrict Traefik's RBAC and namespace watch as a separate reviewed change.

The root Secret contains the private key. Do not paste `kubectl get secret -o
yaml/json` output into chat, terminal transcripts, or a pull request. A
recovery procedure must restore the **same** key and certificate: creating a
new root with the same name does not restore trust on existing clients. This
one-time bootstrap uses a ten-year root validity. Once the Certificate is
deleted, cert-manager cannot automatically renew the offline root; schedule a
trust-anchor replacement before expiry.

The initial portal HTTP routes remain unchanged until leaf certificates,
client trust, and protected access are reviewed and tested. A single control
plane and the local LAN remain availability limits.
