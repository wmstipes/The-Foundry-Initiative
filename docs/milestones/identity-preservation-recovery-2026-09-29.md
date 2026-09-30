# Identity preservation and recovery — September 29, 2026

## Scope and evidence

Preserve the accepted Headlamp/Dex authentication settings through kubeadm
manifest regeneration, and establish private recovery copies. Evidence below
comes from operator-supplied PowerShell/SSH output; it is not an independent
remote cluster inspection. No Kubernetes upgrade or live database restore was
performed. The Istio learning lab remains available.

## Verified recovery checkpoint

- All four nodes were Ready on Kubernetes `v1.36.4`; kubeadm was `v1.36.4`.
- Dex chart `0.24.1`, application `2.44.0`, revision 1, and Headlamp chart
  `0.45.0`, revision 2, each had one Ready replica.
- Expected Dex/Headlamp Secrets existed; the private Headlamp overlay and
  public root CA were present. Secret values were not shared.
- The etcd image was `registry.k8s.io/etcd:3.6.8-0`; both container utilities
  reported `3.6.8`. Snapshot metadata reported storage version `3.6.0`.
- A live snapshot was captured at 19:41:36 UTC on September 29. Inspection
  reported revision `6996143`, 1016 keys, and approximately 17 MB.
- Its off-node Windows copy had 17,203,232 bytes and SHA-256
  `56779577370ab36b1aa57e6bdc0f959f17d28aabc71a4f58f9c41ea660890db3`.
- A checksum-validating `etcdutl snapshot restore` into a separate container
  `/tmp` directory succeeded. No restored server was started. Inspection of
  the reconstructed database retained revision `6996143` and 1016 keys.
  Membership was rewritten; the reported database hash consequently differed.
- The private identity directory and public root were copied into the
  restricted off-node backup directory. The Headlamp overlay hash matched;
  this was not an exhaustive comparison of every private file.
- A control-plane archive was created and listed successfully, then copied
  off-node with matching SHA-256
  `3486af80b8b8c4bc7df65b25603472cde437efd250318b7de4c781b23ab7e779`.
  It contains `/etc/kubernetes`, `/etc/hosts`, `/etc/ssl/certs`,
  `/etc/ca-certificates.conf`, `/usr/local/share/ca-certificates`, and
  `/usr/share/ca-certificates`. This is not a complete node or PV backup.
- API readiness remained `ok` after snapshot capture and offline restoration.

Backups contain credentials and identity keys. They remain in protected
operator storage outside Git. Off-node does not imply encrypted, off-site,
immutable, or automatically refreshed storage. The separate offline root CA
private key is not claimed to be included in these copies.

## Preservation candidate and authorization

The saved kubeadm `ClusterConfiguration` originally had `apiServer: {}`.
The running API server had five OIDC arguments: issuer
`https://auth.forge.home.arpa`, client `headlamp`, username claim `email`,
username prefix `forge:`, and CA file `/etc/ssl/certs/ca-certificates.crt`.
Its host alias mapped the issuer hostname to `192.168.243.250`.

A candidate adds those five arguments to `apiServer.extraArgs`. A strategic
Pod patch preserves the host alias. kubeadm configuration validation and an
API-server-only dry run succeeded with the candidate patch. The generated
manifest diff showed argument order, quoting, indentation, and mapping-order
changes, with no observed change to configuration values, image, probes,
mounts, or security settings.

The live manifest hash remained
`b74502957d83a7d3f67f51b1e351d4c000e8922a2ded34bf957b87d3821a34d2`
before and after rendering. The operator then approved updating only the
saved `ClusterConfiguration` and installing the reviewed patch at
`/etc/kubernetes/forge-kubeadm-patches/kube-apiserver0+strategic.yaml`.
The supplied activation procedure tests the original ConfigMap UID and
configuration before replacing that data field, preserving unrelated fields.

Activation verification passed: the guarded readback procedure checked the
saved configuration against the candidate, the installed patch matched its
reviewed source, and a dry run through the installed patch directory produced
a manifest byte-for-byte equal to the reviewed dry-run candidate. The live
manifest retained its accepted hash and `/readyz` returned `ok`. No live
manifest replacement or API restart was performed. This proves regeneration
with the explicit patch input on kubeadm v1.36.4, not a future-version upgrade.

The patch is owned by root with mode 0644 in a root-owned mode-0755 directory.
Future upgrade commands must include
`--patches /etc/kubernetes/forge-kubeadm-patches`; merely installing the patch
does not arrange automatic use.

## Cleanup acceptance — September 29

After PR #162 merged, the operator rechecked both off-node SHA-256 values;
the snapshot and control-plane archive still matched the recorded hashes.
The temporary snapshot in the etcd data-directory mount was compared with
the retained head-node copy before removal. The two dry-run manifests were
compared before their temporary directories were removed; absence checks
passed for all three staging targets.

The etcd image had no `/bin/rm`. A narrowly scoped host-Python helper instead
verified the retained snapshot hash, located exactly one running etcd process
whose database mount matched the live host database, rejected symlink targets
and the live database, and removed only the known offline-restore directory
through that container's `/proc/<pid>/root/tmp` path. Its absence check passed.

The final API readiness response was `ok`. The etcd Pod was 1/1 Running;
its four restarts were dated 27 days earlier, with no restart caused by this
work. Retained head-node and laptop recovery copies, private identity files,
and installed preservation inputs were not cleanup targets. The audit helper
itself remains with the private recovery material.

## Subsequent outcome — September 30

A separate logical Dex export was restored into an isolated namespace. Content
and RBAC checks passed; recovered Dex served a fresh Headlamp login through an
authorized temporary issuer route. After rollback, original login failed OIDC
signature verification. The same token verified locally and was accepted by the
API after an approved API-server restart with unchanged manifest. Final Pods
were Ready, and Headlamp navigation/refresh succeeded without further prompts.
Three initial BasicAuth prompts remain unexplained. See the
[incident and after-action record](../incidents/2026-09-30-headlamp-oidc-signature-rejection.md)
for timing, diagnostic commands, rotation limits, and remaining work. The recovery
namespace was deleted September 30 at 16:02 EDT after inventory review. Its
absence, original Dex rollout and API readiness checks passed. Private recovery
files were not targeted. No restored etcd server was started and no full cluster
recovery is claimed.

## Remaining acceptance

- Supply the explicit patch directory on every applicable future kubeadm
  upgrade, and repeat the generated-manifest review for the target version.
- Retain updated preservation inputs with the private recovery copies.
- Rehearse whole-cluster recovery separately, with a reviewed recovery
  topology and Kubernetes-aware etcd revision handling. The offline restore
  above did not start etcd or test watch consumers, token validation, fresh
  login, private-file reinstallation, or application PV recovery.
- Revisit the deferred backup cadence after the first central logging increment;
  follow up on the September 30 verifier-state and initial BasicAuth behavior.

See [identity operations](../runbooks/headlamp-oidc.md),
[etcd recovery](https://etcd.io/docs/v3.6/op-guide/recovery/), and
[kubeadm reconfiguration](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-reconfigure/).
