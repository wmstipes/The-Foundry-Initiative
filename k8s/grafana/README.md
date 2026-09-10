# Lightweight Grafana

Milestone 027's accepted design is implemented here for review. **Live deployment and storage preparation are pending.** Do not apply the directory wholesale: the deployment helper orders resources and checks the mounted filesystem first.

## Runtime contract

- Grafana OSS 13.2.1, one replica, `Recreate`, namespace `forge-observability`.
- Verified registry index digest: `sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283`.
- Verified Linux ARM64 manifest: `sha256:a2b9816a8dd62be7ad47ae6d1ea8894cd88742d3588872fa01bff83e79bcb17a`.
- Registry image configuration specifies user `472`; tagged Dockerfile defaults to group `0`. The storage-preflight Pod verifies runtime UID/GID 472:0 before first deployment.
- Requests: 100m CPU / 512Mi memory; limits: 1000m CPU / 1Gi memory.
- Non-root, no API token, no RBAC, no capabilities, read-only root filesystem. Persistent data and bounded temporary files are the writable paths.
- ClusterIP on port 3000 with localhost-only operator forwarding.
- No additional plugin installation, anonymous access, sign-up, snapshots, or alert evaluation.

The [13.2.1 release](https://github.com/grafana/grafana/releases/tag/v13.2.1), [security advisories](https://grafana.com/security/security-advisories/), [tagged Dockerfile](https://github.com/grafana/grafana/blob/v13.2.1/Dockerfile), and [registry tag metadata](https://hub.docker.com/v2/repositories/grafana/grafana/tags/13.2.1) were reviewed on 2026-09-10. ARM64 configuration was retrieved from the registry by digest. This verifies published image metadata, not a running container or a complete vulnerability scan. Browser and ARM64 startup acceptance remain pending.

## First step on the NUC

From a normal PowerShell session in the reviewed repository checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\get-grafana-preflight.ps1
```

This invocation changes execution policy only for that process. It reads cluster state and SSH host inventory; it does not deploy workloads, modify partitions, or read Secret contents. SSH uses existing trusted host records with strict verification. Inspect the context, Ready nodes, allocatable resources and allocated requests, control-plane taint, CoreDNS suffix, NetworkPolicies, StorageClass, Prometheus storage, NVMe health, and unused disk extents.

The agent's task session could read the repository but could not write its original Git metadata or use the workstation's kubectl/SSH files despite permission grants. The implementation was therefore prepared in an isolated checkout. Do not treat its local validation as evidence of live cluster readiness.

## Storage preparation gate

Review the live inventory before writing a partition command. The required allocation is a new 4 GiB ext4 partition in verified unused space on Samsung SSD 950 PRO serial `S2GMNCAGB06236R`. The existing 32 GiB Prometheus partition must keep its boundaries, UUID `4f2feee5-72a7-4f32-a351-b4253c4a0854`, data, and mount intact. The recorded historical media-error count was 215; investigate any increase or new critical warnings before continuing.

The operator's 2026-09-10 inventory confirmed the unused extent begins at sector 67110912. The prepared helper allocates exactly 8388608 sectors there (4 GiB), ending at sector 75499519. It requires the reviewed one-partition layout and rechecks it before writing. It does not erase the disk or recreate the Prometheus filesystem.

Run `scripts/prepare-grafana-storage.ps1` without switches to verify the accepted off-node Prometheus archive and save the current partition table to the NUC. Supply `-Prepare` to continue through new partition creation, ext4 formatting, UUID mounting, ownership/write checks, and missing-mount verification. The default archive is the exact six-block Milestone 026 acceptance archive with its recorded SHA-256. A missing or mismatching archive stops the helper before disk writes. The helper captures a fresh partition table off-node before each attempt and refuses an existing partition 2. If preparation stops after a partial write, retain its output for review; do not rerun, erase, or format again.

The helper uses `sfdisk --append` with exact sectors and explicit no-reread/no-tell-kernel flags, then adds only partition 2 to the kernel with `partx`. It checks the new kernel geometry before formatting. See the upstream [sfdisk](https://man7.org/linux/man-pages/man8/sfdisk.8.html) and [partx](https://man7.org/linux/man-pages/man8/partx.8.html) manuals. This procedure's live result remains pending.

Current operator progress: filesystem preparation is complete. Partition 2 has PARTUUID `a8e50bc1-1b9c-419b-a13d-3ee72c29ff56` and ext4 filesystem UUID `a506c674-127a-46da-9c7d-d158b6d1bb75`. It is mounted at `/mnt/signalforge-grafana`; data ownership, writes, UUID mounting and missing-mount verification passed. Do not rerun either storage preparation helper. The earlier partial-formatting gate failure and its correction remain recorded in Milestone 028.

Mount the new filesystem by UUID at `/mnt/signalforge-grafana`. Create its `data` directory only after the mount is verified; assign owner `472:0` and mode `0750`. Confirm a write using that identity. Unmount the **new Grafana filesystem only**, prove `/mnt/signalforge-grafana/data` disappears, then remount and verify UUID. Configure persistent mounting before workload startup. Record the new UUID and partition boundaries in Milestone 028.

`grafana-local-nvme` advertises 3 GiB; the physical 4 GiB partition supplies isolation. Kubernetes local-PV capacity is not a hard filesystem quota. Review usage weekly at 70 percent and act before 85 percent. Reuse the existing retained `signalforge-local-nvme` class; the helper does not modify that shared class.

## Credentials

Create a protected recovery directory outside Git. Use the following with your verified context and an unused recovery filename:

```powershell
.\scripts\new-grafana-secret.ps1 -ExpectedContext '<verified context>' -RecoveryFile '<protected directory>\grafana-recovery.xml'
```

The helper prompts for the username and password without echoing the password, generates a separate encryption key, and creates `grafana-admin` without putting secret values in command arguments or tracked files. The recovery XML encrypts SecureString fields with Windows DPAPI; it can only be decrypted by that Windows user on that machine. Keep an independent password-manager copy of both password and encryption key before acceptance. Do not rely on the DPAPI file alone for recovery after NUC loss. Do not paste secrets into this task.

The helper refuses to overwrite an existing Secret or recovery file. After initialization, rotate a user's password through Grafana; merely updating the bootstrap Secret does not change the database password. Preserve the matching encryption key with recovery records. Changing that key needs Grafana's documented encryption-migration procedure.

## Review and deploy

Run the repository validator from its root, with the existing pinned PyYAML dependency:

```powershell
python .\scripts\validate-k8s-manifests.py
```

Review the six resource manifests and four configuration directories. Use server-side dry runs for the standalone manifests after the namespace exists. Review live diffs only for Grafana resources; `kubectl diff` returns 1 for differences and greater than 1 for an error. Do not interpret every nonzero diff exit as a failure.

After storage, runtime capacity, credentials, and the configuration review pass:

```powershell
.\scripts\deploy-grafana.ps1 -ExpectedContext '<verified context>' -ExpectedFilesystemUuid '<new Grafana filesystem UUID>'
```

The helper verifies the context, mount UUID, Secret key presence, and shared StorageClass. It applies the retained volume and claim, runs a temporary write-check Pod on first installation, waits for its successful exit, and verifies the claim is bound to the intended volume. It then generates ConfigMaps from the source directories, applies the Service and Deployment, and waits for readiness. Updates restart the existing Grafana Pod so settings and data-source changes take effect. A failed preflight prevents starting Grafana.

Configuration changes are sourced from Git. The two dashboards poll projected directory mounts every 30 seconds after ConfigMap propagation. Settings and data-source changes require a restart. No `subPath` mounts or watching sidecar are used. Dashboard UIDs and the data-source UID are stable.

## Access and validation

```powershell
.\scripts\open-grafana.ps1 -ExpectedContext '<verified context>'
```

Open `http://127.0.0.1:3000`. In another PowerShell window:

```powershell
.\scripts\test-grafana.ps1
```

The tester checks health/version, rejection of anonymous dashboard search, data-source provisioning, exactly two dashboards with six panels each, every panel query through Grafana's Prometheus proxy, and three healthy API targets. Password input uses the credential prompt. Do not log request headers or run a transcript that captures manually exposed secrets.

Inspect the dashboard layout and units in the browser. Exercise known application paths over at least two scrape intervals and verify traffic and latency; inspect the unmatched-route panel with a bounded 404 exercise. Zero-traffic and missing-data intervals must not be rendered as zero latency or healthy zero errors. Fixture tests cover the error-ratio edge cases without forcing live application failures.

Record a preference or other database-backed state, delete only the Grafana Pod, wait for its replacement, and confirm that state survives. Observe two dashboards for 30 minutes with periodic `kubectl top pods -n forge-observability`; record peak sampled usage, restarts, target health and any dashboard loads above five seconds. Grafana memory repeatedly above 80 percent of the limit requires investigation. Do not call a handful of samples a continuous peak measurement.

## Backup

Prepare encrypted, access-controlled storage on the NUC outside Git, normally `C:\Users\Michael Stipes\SignalForge-Backups\grafana`. Verify its encryption and available space before supplying the explicit switch:

```powershell
.\scripts\backup-grafana.ps1 -ExpectedContext '<verified context>' -BackupDirectory 'C:\Users\Michael Stipes\SignalForge-Backups\grafana' -EncryptedDestinationVerified
```

The helper stops only Grafana, waits for its Pods to disappear, uses a read-only mount to archive the complete data directory, copies the archive off-node, and compares SHA-256. The temporary archive uses at most 3 GiB of node ephemeral storage; check that space beforehand. Cleanup attempts to remove the helper and restore one Grafana replica even if backup fails. A copied `.partial` is not an accepted backup. Verify login and dashboards afterward.

Keep four successful weekly archives and the latest accepted pre-upgrade archive (use `-PreUpgrade`). Retention is deliberately manual; the script deletes no backups. Record image digest, Git state, Grafana PV/PVC, filesystem UUID, credential-recovery availability, and post-backup acceptance alongside the generated checksum metadata. If the checkout is dirty, the commit alone does not capture the running configuration: preserve the reviewed diff and exact configuration as well.

## Isolated service restore

Use an archive with its `.json` checksum sidecar and the same protected encryption key used at backup time. The helper uses current provisioned configuration, so first verify it matches the backup-era configuration (mandatory for upgrade rollback testing). The restore image comes from the backup's pinned image field.

```powershell
.\scripts\restore-grafana-isolated.ps1 -ExpectedContext '<verified context>' -Archive '<verified backup path>'
```

The temporary Pod mounts **no production PVC**: restored data and archive use bounded `emptyDir` volumes. Reserve up to 7 GiB of temporary node space plus image space. It uses a distinct label and no Service, so the production Grafana Service cannot route to it. It can query the existing Prometheus Service without changing collection. If the backup needs a different preserved key, provide a separate recovery Secret with `-RecoverySecretName`.

Forward the temporary Pod on localhost port 3001 using the command printed by the helper. Run `test-grafana.ps1 -Port 3001`, verify login and persisted preferences in the browser, and record time from recovery start through usable dashboards. Startup time alone is not RTO. Delete only `pod/grafana-restore-validation` when finished. The helper retains the isolated Pod on failure for inspection.

## Rollback and recovery boundaries

First-install rollback: scale `deployment/grafana` to zero and retain PV, PVC, data, Secret and configuration. Verify Prometheus remains healthy, then reapply Grafana and verify the returned state. Never delete `forge-observability`, its shared StorageClass, or any Prometheus resources.

Upgrade rollback requires a compatible image, configuration and pre-upgrade database copy. Protect the failed state before replacing any data. The isolated restore helper never performs an in-place overwrite. Rehearse recovery before implementing any destructive live restore.

Weekly backup and 7-day RPO are manual responsibilities. The one-hour RTO objective assumes a functioning cluster and prepared replacement storage; full head-node/NVMe reconstruction remains outside that timing. No persistence, resource-soak, restore or rollback result is claimed until the corresponding live test is recorded.
