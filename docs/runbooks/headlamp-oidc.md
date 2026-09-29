# Headlamp identity operations

**Accepted pilot:** 2026-09-28. See the [rollout evidence](../milestones/private-access-and-headlamp-oidc.md).

## Current contract

Dex chart `0.24.1` runs one replica with Kubernetes storage. Headlamp chart
`0.45.0`, release revision 2 at acceptance, uses an external OIDC Secret and a
public CA mount supplied by a private Helm overlay. The API server trusts the
same issuer and client ID, maps the verified email claim with an explicit
username prefix, and authorizes that user through `view` and scoped Node reads.
The BasicAuth ingress gate is still present. Other portal applications have
their own authentication; this pilot does not establish shared SSO for them.

## Private recovery material

Keep the following outside the public repository, in protected operator
storage with an independently recoverable copy:

- Dex configuration, account identifiers and password hashes, OIDC client ID,
  client secret, issuer, and registered callback URL.
- Headlamp's private values overlay, public CA certificate, and separately
  created OIDC user RBAC bindings. Its base chart values alone are insufficient.
- The original and accepted API-server manifests with their verified hashes;
  host trust and name-resolution changes; the intended kubeadm configuration
  and patches for future upgrades.
- A reviewed backup of Kubernetes state containing Dex storage and Secrets.
  A copy of the API-server Pod manifest does not contain that state.
- The existing administrator kubeconfig and trusted SSH/console access, stored
  securely and independent of the Dex browser login.

On September 29, an off-node etcd snapshot and control-plane archive passed
SHA-256 transfer verification, and an offline etcd reconstruction retained
the snapshot revision and key count. Private identity files were copied too.
See the [recovery evidence and limits](../milestones/identity-preservation-recovery-2026-09-29.md).
No restored etcd server or recovered Dex login was exercised. Do not equate
offline database reconstruction with recovery after loss of the control plane.

## Diagnose a login failure

| Observation | Check next |
| --- | --- |
| Name cannot resolve | Client hosts/DNS, then the control-plane and Headlamp Pod's configured resolution |
| Certificate error | Correct issuer hostname, valid chain, expiry, and public root trust at the failing client |
| Browser BasicAuth rejects access | Headlamp's ingress middleware and its separate credential Secret |
| Dex discovery fails | Identity Deployment, Service endpoints, gateway route and ingress policy |
| Callback fails | Exact registered callback, matching client ID/secret, and Headlamp CA mount |
| Dex sign-in works but cluster rejects the session | API-server issuer/audience, clock, trust, prefixed username, and user RBAC |
| API is unavailable after configuration change | Direct SSH/console recovery using the verified pre-change manifest |

Inspect rollout status and bounded logs for the component at fault. Keep
passwords, hashes, client secrets, tokens, cookies, authorization codes, and
full callback URLs out of shared logs. Do not disable TLS verification to
make a failing login pass.

## Upgrades and rollback

Use the [Headlamp runbook](../../k8s/headlamp/README.md) with both values files.
Render and compare first; confirm the external Secrets exist without printing
their contents. After rollout, use a fresh browser session to exercise the
actual OIDC path rather than relying on a previously stored token. Retest the
expected read-only identity. Impersonation verifies RBAC for a username; it
does not test issuer authentication or what a browser token actually claims.

Record the previous Helm revision and its values before an upgrade. A Helm
rollback changes Headlamp only; it does not restore a rotated Secret, Dex
configuration, identity data, or API-server authentication settings.

### Preserve OIDC during kubeadm upgrades

On September 29, the accepted five OIDC flags were recorded in the
`apiServer.extraArgs` list of `kube-system/kubeadm-config`'s
`ClusterConfiguration`. The issuer host alias is retained in the root-owned
`/etc/kubernetes/forge-kubeadm-patches/kube-apiserver0+strategic.yaml` on
`forge-head`. The installed inputs regenerated the reviewed API manifest in
kubeadm v1.36.4 dry-run mode, without replacing the running manifest.

**The patch directory is not automatically discovered.** Every applicable
control-plane upgrade must explicitly supply
`--patches /etc/kubernetes/forge-kubeadm-patches`, or an equivalently reviewed
`UpgradeConfiguration` patch-directory setting. This project has not installed
an upgrade wrapper or claimed automatic enforcement. Worker-only steps follow
their own upgrade procedure; this patch is for the control-plane API Pod.

For a separately approved upgrade, set `targetVersion` to the reviewed version
on `forge-head`, verify current backups and independent administrator/SSH
access, inspect the saved kubeadm configuration and patch, and review the
upstream upgrade prerequisites. The following is the command shape, not an
instruction to upgrade now:

```bash
# First render and review; targetVersion must be deliberately set beforehand.
sudo kubeadm upgrade apply "${targetVersion:?Set the reviewed target version}" \
  --patches /etc/kubernetes/forge-kubeadm-patches --dry-run
# Only after accepting that diff and approving the upgrade:
sudo kubeadm upgrade apply "${targetVersion:?Set the reviewed target version}" \
  --patches /etc/kubernetes/forge-kubeadm-patches
```

Check that generated arguments retain the issuer, client `headlamp`, email
claim, `forge:` prefix, and CA file; that the issuer host alias remains; and
that certificate host mounts, image, security settings and probes have only
reviewed changes. Preserve the trusted public root on the host too: preserving
a mount does not recreate its contents. Validate readiness and fresh OIDC
login after an actual upgrade. An unchanged current-version dry run does not
prove compatibility with a future kubeadm or API-server release.

The preservation-only change did not restart the API server. To undo that
change before an upgrade, restore only the saved `ClusterConfiguration` data
field with a check that the current value still matches the accepted candidate,
and remove only the installed OIDC patch after verifying it is the expected
file. Do not replace the whole ConfigMap from stale exported metadata. This
undoes future regeneration inputs; it does not remove OIDC from the running
API server. A failed live upgrade needs the separate reviewed control-plane
recovery plan, not merely this ConfigMap rollback.

See [reconfiguration](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-reconfigure/)
and [component customization](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/control-plane-flags/).

### Live manifest recovery

For an approved API-server change, retain SSH/console access and a verified
backup. Stage candidate and restore files **outside**
`/etc/kubernetes/manifests`; use an atomic move from the same filesystem to
replace the live manifest. Keep backup files out of that watched directory.
Check `/readyz` and that the new Pod actually has the intended configuration;
readiness from the old Pod is insufficient. If startup fails, restore the
verified original through SSH and verify recovery before further changes.
See Kubernetes' [static Pod guidance](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/).

The earlier local ServiceAccount token flow is retained as a potential
Headlamp recovery path but has not been retested after OIDC. Do not treat it as
a demonstrated identity-outage recovery procedure.
