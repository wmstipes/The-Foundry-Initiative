# Milestone 026 - Persistent Prometheus Storage

Started: 2026-09-09

Status: In progress

## Goal

Implement and validate the static local-PV design approved in Milestone 025. Prometheus must write to the `forge-head` NVMe rather than an SD card, retain its history across Pod replacement, stay ClusterIP-only, and have an off-node recovery path.

## Implementation state

The host-storage gate is complete. The repository now contains the StorageClass, pre-reserved local PV and PVC, Prometheus PVC cutover, guarded deployment helper, static configuration validator, and live storage and persistence checks.

The Kubernetes cutover is live. PVC binding and its write test preceded cutover. Pod-replacement persistence and off-node backup/restore validation have passed. Port-forward verification and rollback testing remain open.

## Physical inventory correction

The planning input described a 2 TB Samsung 970 EVO Plus. The required live inventory instead found:

| Item | Verified value |
|---|---|
| Node | `forge-head` |
| Device | `/dev/nvme0n1` |
| Model | Samsung SSD 950 PRO 512GB |
| Serial | `S2GMNCAGB06236R` |
| Capacity | 512,110,190,592 bytes (476.94 GiB) |
| Firmware | `1B0QBXX7` |
| Prior layout | Windows GPT with recovery, EFI, reserved, and NTFS data partitions |
| Root device | `/dev/mmcblk0p2`, confirming the NVMe was not the active OS disk |

The operator explicitly chose to erase the entire verified 950 PRO for SignalForge and entered the device-specific confirmation `ERASE-S2GMNCAGB06236R`.

Before repartitioning, the prior table was saved as `/home/wmstipes/nvme0n1-before-signalforge.sfdisk` with SHA-256:

```text
091ce04e23ce1eb886bf30e5af07a739a9f104062e5d9b10f5db8d370f4af01f
```

## NVMe health gate

`nvme-cli` reported zero critical warnings, 99 percent available spare, 2 percent used endurance, 305 K temperature, and 215 historical media errors. The device does not support the optional NVMe self-test command. Its error-log entries were invalid or unsupported administrative-command records rather than observed LBA failures, and the kernel log contained no NVMe I/O errors, resets, timeouts, or PCIe AER failures.

Because the historical media-error count was non-zero, the complete empty 32 GiB target partition received a destructive four-pattern `badblocks` write/read test. All patterns completed with zero bad blocks and zero read, write, or compare errors. The NVMe media-error count was 215 both before and after the test.

This drive is accepted for noncritical lab metrics with the planned off-node backups. It is not treated as the only recovery copy.

## Host storage created

| Item | Implemented value |
|---|---|
| GPT disk GUID | `FDF2C7FC-C23E-4147-93B5-B53D85A08F78` |
| Partition | `/dev/nvme0n1p1` |
| Partition size | 32 GiB |
| GPT partition name | `signalforge-prometheus` |
| GPT partition UUID | `4811522e-21c3-4fae-ae0d-835ac0299fc3` |
| Filesystem | ext4, 4 KiB blocks |
| Filesystem label | `sf-prometheus` |
| Filesystem UUID | `4f2feee5-72a7-4f32-a351-b4253c4a0854` |
| Mount point | `/mnt/signalforge-prometheus` |
| Mount options | `defaults,noatime` |
| Kubernetes local path | `/mnt/signalforge-prometheus/data` |
| Data directory | `65534:65534`, mode `0750` |

The persistent `/etc/fstab` entry is:

```text
UUID=4f2feee5-72a7-4f32-a351-b4253c4a0854 /mnt/signalforge-prometheus ext4 defaults,noatime 0 2
```

`findmnt`, `df`, `blkid`, and `findmnt --verify` confirmed the expected ext4 source and UUID. A write test as UID and GID 65534 succeeded. The filesystem was then unmounted deliberately; the `data` path disappeared rather than resolving to the SD-backed root filesystem. The filesystem remounted successfully afterward.

## Kubernetes implementation

The repository implementation defines:

- Non-default StorageClass `signalforge-local-nvme`
- `kubernetes.io/no-provisioner`, `WaitForFirstConsumer`, and `Retain`
- Static local PV `prometheus-local-nvme` with 30 GiB capacity
- Exact `forge-head` hostname node affinity
- PV reservation for `forge-observability/prometheus-data`
- Matching PVC with explicit `volumeName`
- One Prometheus replica using `Recreate`
- Only the required control-plane `NoSchedule` toleration
- PVC-backed `/prometheus` storage
- Retention of 30 days or 24 GB, whichever is reached first
- ClusterIP-only service access

The deployment helper applies the storage objects first and refuses to update the existing Prometheus Deployment unless the named PVC is `Bound` to the named PV.

## Remaining acceptance checks

- [x] Verified the exact physical device and protected the previous partition table.
- [x] Received explicit device-specific authorization before destructive work.
- [x] Completed destructive media testing without new media errors.
- [x] Created and verified the dedicated ext4 filesystem and UUID mount.
- [x] Verified runtime ownership, writes as UID/GID 65534, and missing-mount fallback protection.
- [x] Confirmed the live control-plane `NoSchedule` taint on `forge-head`.
- [x] Added the static StorageClass, PV, PVC, Prometheus cutover, and validation tooling to the repository.
- [x] Bind the PVC to the intended retained PV before the workload cutover.
- [x] Verify Prometheus is Ready on `forge-head` with 30-day/24-GB retention.
- [x] Verify three healthy Restaurant API targets.
- [x] Verify a known historical sample survives Prometheus Pod replacement.
- [ ] Confirm Prometheus remains ClusterIP-only and port-forward access still works.
- [x] Create an off-node cold backup and complete a non-destructive restore-validation drill.
- [ ] Test and document rollback without deleting or altering retained PV data.
- [ ] Update current-state documentation and complete the milestone.

## Operator acceptance evidence through 2026-09-10

Deployment checks confirmed one Ready Prometheus Pod on `forge-head`, the bound 30 GiB retained PV/PVC, 30-day/24-GB retention, ClusterIP-only access, and three healthy targets. Pod replacement recovered the exact `up` sample for `restaurant-api-6dfbf8dd9b-4nnlb`: value `1`, timestamp `1788988641.573`.

Acceptance archive on the Windows NUC:

```text
C:\Users\Michael Stipes\SignalForge-Backups\prometheus\prometheus-tsdb-20260910-150206Z.tar.gz
Bytes: 477532
SHA-256: 68e00637d6fd05db21bc8e5dbefa7bbb7d65a7548dd3de0eec5c2faae574dc24
Compacted blocks: 6
```

Cold backup restored the collector to one replica and three healthy targets. Restore validation verified the checksum, extracted into `/mnt/signalforge-prometheus/restore-validation`, checked WAL presence and metadata, listed all six blocks, and analyzed newest block `01M25XAGEKB8AJ22F53Y9K0YMP` with 309 series. Isolated-copy cleanup passed; active data and the archive were retained.

The drill demonstrates isolated extraction and block analysis, not full service restoration, archived WAL replay, a measured one-hour RTO, or rollback to ephemeral storage. Weekly backups remain an operator procedure rather than a scheduled job.

Acceptance exposed two helper defects, now corrected: readiness reads `/metrics` directly because this collector does not scrape itself; restore checks use direct commands to avoid Windows PowerShell nested-shell quoting failures. The earlier WAL-only backup is separate from this six-block acceptance archive.
