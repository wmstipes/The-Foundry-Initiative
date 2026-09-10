# Milestone 028 Lightweight Grafana

Started: 2026-09-10

Status: Implementation prepared; live preflight and deployment pending

## Goal

Implement the Grafana design accepted in Milestone 027 and collect runtime, dashboard, persistence, backup, restore, resource-budget and rollback evidence.

## Prepared implementation

- Six standalone manifests for Grafana's account, Service, retained local PV, PVC, preflight Pod and Deployment.
- Pinned Grafana OSS 13.2.1 image with verified published ARM64 metadata.
- One replica, `Recreate`, 100m/512Mi requests and 1000m/1Gi limits.
- No Kubernetes API token or RBAC, non-root runtime, restricted container privileges, and directory-mounted configuration.
- Four source directories for deterministic ConfigMap creation, including two dashboards with twelve panels and scoped PromQL.
- PowerShell preflight, credential, deployment, access, query-check, cold-backup and isolated-restore helpers.
- Static deployment-boundary validation, negative regression tests and promtool query fixtures added to manifest CI.

## Image evidence

Registry metadata retrieved on 2026-09-10:

- Index: `sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283`
- Linux ARM64 manifest: `sha256:a2b9816a8dd62be7ad47ae6d1ea8894cd88742d3588872fa01bff83e79bcb17a`
- Image configuration: OS `linux`, architecture `arm64`, user `472`, entrypoint `/run.sh`.
- Tagged Dockerfile default group: `0`; runtime `id` verification remains part of the storage-preflight Pod.

The upstream release and current security advisories were reviewed. This is not a vulnerability-scan result or an ARM64 startup test.

## Local verification

Local verification passed on 2026-09-10: the complete repository manifest validator, seven Grafana boundary regression tests, all thirteen panel expressions and four error-ratio edge cases under promtool 3.13.2, and parser checks for all eight Grafana PowerShell files. No local result substitutes for the checks below. In particular, PowerShell parsing is not execution against a real cluster.

The PromQL fixtures check all panel expressions against absent input plus error-percentage cases for positive traffic without errors, 10 percent errors, idle traffic, and a very low positive rate. The fixtures avoid generating failures in the live Restaurant API.

## Access limitation

The agent session could read the original repository at `653ffa6`, but original Git writes, trusted SSH files, and the supplied kubectl executable remained denied despite permission grants. Work continued in an isolated checkout on `codex/milestone-028-lightweight-grafana`. The original repository and live cluster have not been modified. No new partition exists as a result of this work.

The operator returned the read-only preflight output on 2026-09-10. Its findings are recorded below. Storage preparation is the next operation; no partition-write result has yet been supplied.

## Operator preflight evidence

- Context: `kubernetes-admin@kubernetes`; all four nodes Ready and ARM64.
- Head taint: `node-role.kubernetes.io/control-plane:NoSchedule`, matching the narrow toleration.
- Head requests before Grafana: 950m CPU and 496Mi memory. Grafana would bring requests to 1050m and 1008Mi, within reported allocatable capacity. Observed head usage: 153m CPU / 2664Mi memory, with no resource-pressure conditions.
- CoreDNS suffix `cluster.local` matches the data-source URL. No native Kubernetes NetworkPolicy resources were returned; this does not inventory Calico-specific global policies.
- Prometheus remains one Ready Pod with zero restarts; ClusterIP Service and retained 30 GiB PVC/PV are intact. This inventory did not query the live Prometheus targets API.
- NVMe serial/model match the accepted device; critical warning 0, spare 99 percent, used endurance 2 percent, media errors 215 (unchanged).
- GPT ID `FDF2C7FC-C23E-4147-93B5-B53D85A08F78`; 512-byte sectors; existing partition 1 starts at 2048, spans 67108864 sectors, and retains PARTUUID `4811522e-21c3-4fae-ae0d-835ac0299fc3` and filesystem UUID `4f2feee5-72a7-4f32-a351-b4253c4a0854`.
- Verified unused extent: sectors 67110912 through 1000215182, approximately 444.94 GiB.
- Exact proposed partition 2: start 67110912, length 8388608 sectors, end 75499519 (4 GiB). This starts immediately after partition 1 and is aligned to 1 MiB.

The helper's final `exit` arrived as `exit\r` because Windows PowerShell appended CRLF to SSH stdin. Host inventory had completed before that failure. The helper now strips carriage returns on the remote input stream; a regression test reproduces and validates Windows line endings. Its `findmnt --verify` call now uses sudo so block-device permission warnings do not obscure the result. The user output had zero parse errors and zero errors, with three non-root permission warnings.

The new standalone `prepare-grafana-storage.ps1` verifies the six-block Prometheus archive checksum on the NUC, saves and checksums the current partition-table backup off-node, rechecks serial/UUID/layout/health, then creates only the reviewed new extent when `-Prepare` is supplied. It tests new filesystem writes and missing-mount behavior and records the new UUID. It never creates Kubernetes resources. Any partial failure requires inspection before retry; it refuses an existing partition 2 rather than reformatting it.

After this correction, nine regression tests, Bash syntax checks, PowerShell parsing and the allocation arithmetic checks pass locally. Host mutation has not been executed by the agent.

## First storage preparation attempt

The operator verified the known Prometheus archive and saved the current partition table off-node at `C:\Users\Michael Stipes\SignalForge-Backups\storage\grafana-20260910-161711Z`. The host script then stopped in its initial SMART JSON check with `KeyError: available_spare`. That check precedes host backup-directory creation, partition-table modification, formatting and mounting, so this attempt made no disk-layout or filesystem changes.

The helper had incorrectly used the human-readable field name. nvme-cli's JSON uses `avail_spare`; verbose JSON can additionally represent `critical_warning` as an object with a `value` member. Both pre-write and post-write gates now use those documented fields and retain the same health thresholds. Six new regression tests exercise both gates against valid numeric/verbose output, missing spare information, reduced spare capacity, increased media errors, and a critical warning. No health check has been bypassed. The corrected helper still verifies the original one-partition layout and refuses an existing partition 2 before writing.

Field reference: [Debian nvme-cli JSON implementation](https://sources.debian.org/src/nvme-cli/2.13-2/nvme-print-json.c/).

## Partition creation and filesystem resume

The second operator attempt saved evidence at `C:\Users\Michael Stipes\SignalForge-Backups\storage\grafana-20260910-161938Z` and host directory `/var/tmp/signalforge-grafana-storage.Hif8pE`. It created partition 2 at start 67110912, length 8388608 sectors, with PARTUUID `a8e50bc1-1b9c-419b-a13d-3ee72c29ff56`. Partition 1's boundaries remained unchanged. The dry-run output preceded the real partition-table update; the printed partition-3 prompt was not a third created partition.

The helper stopped before `mkfs.ext4` because `blkid -p` returned GPT `PART_ENTRY_*` metadata with success status. The code had incorrectly required exit 2 for an unformatted partition. The corrected gate uses `--no-part-details`, requires empty output and exit 0 or 2, and rejects detected filesystem signatures, ambiguity and errors. It does not merely discard nonzero status. Reference: [blkid probing and exit status](https://man7.org/linux/man-pages/man8/blkid.8.html).

Use `finish-grafana-storage.ps1 -Finish` for this specific partial state. It verifies both partitions, the observed partition-2 PARTUUID, kernel geometry, disk identity, preserved Prometheus filesystem, health, and the off-node backup before formatting. It contains no partition-table mutation or kernel partition-add command. Existing filesystem content or an existing mount directory stops it. Original creation helper retries are inappropriate now that partition 2 exists.

Both corrected signature gates passed six mocked result cases each; the resume helper passed Bash and PowerShell syntax checks and a regression check excluding repartitioning commands. Formatting, mounting and the new filesystem UUID remain pending operator output.

## Filesystem preparation completed

The operator's completion output confirms ext4 filesystem UUID `a506c674-127a-46da-9c7d-d158b6d1bb75` on `/dev/nvme0n1p2`, mounted at `/mnt/signalforge-grafana` with `rw,noatime`. The data directory is owned by `472:0` with mode `0750`. Reported capacity is 3.9G with 3.7G available. Both partition boundaries and their PARTUUIDs remain as expected; the Prometheus partition is preserved.

The completion script reached its final success marker after the write check, unmount/missing-data-path check, remount, UUID-based fstab entry, root-level mount verification and final media-health checks. This verifies those host gates; it does not prove Kubernetes Pod persistence. `mke2fs`'s version banner appeared as a PowerShell NativeCommandError record because it was written to stderr, but the SSH operation completed successfully and no terminating failure followed.

Evidence: NUC directory `C:\Users\Michael Stipes\SignalForge-Backups\storage\grafana-20260910-162247Z`; host directory `/var/tmp/signalforge-grafana-storage.RUbKr3`. No Kubernetes objects were created by the storage helper. The next step is to apply the implementation patch on a focused repository branch, create the protected bootstrap Secret, and run the gated deployment helper using the verified context and filesystem UUID. Do not run either formatting helper again.

## Live acceptance still required

- [x] Inventory and health authorize an exact unused 4 GiB allocation; current partition table and Prometheus backup are protected off-node.
- [x] New UUID-mounted filesystem, ownership and missing-mount protection pass; Prometheus boundaries and UUID remain intact.
- [x] Context, DNS suffix, taint, resource capacity and shared StorageClass match the reviewed configuration.
- [ ] Credentials are created and independently recoverable outside the NUC-only DPAPI file.
- [ ] Server-side manifest checks, apply diff and runtime UID/GID preflight pass; PVC binds to `grafana-local-nvme`.
- [ ] Grafana becomes Ready on `forge-head`; authenticated localhost forwarding works and anonymous access fails.
- [ ] Two dashboards, twelve panels and all queries pass; browser layout, idle states, missing data and failure states are inspected.
- [ ] Pod replacement preserves accounts and a known database-backed preference.
- [ ] Thirty-minute observation records resource use, dashboard response time, no OOM/restarts and healthy Prometheus collection.
- [ ] Cold backup verifies off-node; isolated Grafana restore passes login, preferences and queries, with measured recovery time.
- [ ] Initial rollback and return pass while preserving retained storage and all Prometheus resources.
- [ ] Update this milestone and current-state documentation with actual evidence, limitations and completion status.

See `k8s/grafana/README.md` for the ordered operator procedure and Milestone 027 for the full acceptance contract.
