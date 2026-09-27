# Forge private CA: completed bootstrap and offline root

The cluster runs cert-manager v1.21.2 (Helm release `cert-manager`, namespace
`cert-manager`, CRDs managed with `crds.enabled=true`). The root was generated,
backed up, used to sign the gateway intermediate, and removed from the cluster.
The `forge-gateway-ca` Issuer and `forge-gateway-tls` Certificate are Ready in
`forge-gateway`. No root key or issued Secret belongs in Git.

**The bootstrap files below record one-time operations. Do not reapply
`root-bootstrap.yaml` or `gateway-ca-bootstrap.yaml` to the running cluster.**
The former would generate a different root; the latter would recreate a root
signer without its offline key.

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

The one-time bootstrap manifests are retained for audit. Recovery must restore
the original backed-up Secret under controlled conditions; the historical
`kubectl apply` sequence would create a new, untrusted root on this cluster.

During bootstrap, the Traefik ServiceAccount could list Secrets in
`cert-manager` (confirmed live). Removing the root Secret after issuance
reduced its exposure. Restrict Traefik's RBAC and namespace watch as a
separate reviewed change.

The root Secret contains the private key. Do not paste `kubectl get secret -o
yaml/json` output into chat, terminal transcripts, or a pull request. A
recovery procedure must restore the **same** key and certificate: creating a
new root with the same name does not restore trust on existing clients. This
one-time bootstrap uses a ten-year root validity. Once the Certificate is
deleted, cert-manager cannot automatically renew the offline root; schedule a
trust-anchor replacement before expiry.

The gateway now serves the private certificate from a Traefik TLSStore. The
laptop trusts the public root certificate; HTTP redirects to HTTPS; the portal,
Workbench, and Restaurant routes verified over HTTPS. The root certificate file
hash used before import was
`68105417902A1EF6C0905DF6923774E0DEB3BB59EAF83B21E1E41651CB874106`.
The NUC still needs a separately verified public-root import. Headlamp,
Grafana, Prometheus, and Service Pulse remain unexposed pending authentication.
A single control plane and the local LAN remain availability limits.
