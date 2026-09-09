# Milestone 025 - Persistent Prometheus Storage Planning

Started: 2026-09-09

Completed: 2026-09-09

Status: Complete

## Goal

Choose a safe, lightweight persistent-storage design for Prometheus before changing the live collector. The design must favor the head-node NVMe over SD-card writes, make node-failure behavior explicit, and define capacity, retention, backup, recovery, migration, and rollback expectations.

## Result

Selected a statically provisioned Kubernetes `local` PersistentVolume backed by a dedicated ext4 partition on the Samsung 970 EVO Plus NVMe attached to `forge-head`.

This milestone records the decision and implementation gate only. It does not partition the NVMe, create Kubernetes storage resources, or change the live Prometheus Deployment. Prometheus continues to use its existing 1 GiB `emptyDir` until Milestone 026 is deliberately executed and validated.

## Selected design

| Item | Decision |
|---|---|
| Storage device | Samsung 970 EVO Plus NVMe on `forge-head` |
| Physical allocation | Dedicated 32 GiB partition |
| Filesystem | ext4 |
| Host mount point | `/mnt/signalforge-prometheus` |
| Mount identity | Filesystem UUID rather than a device name |
| Kubernetes volume | Statically provisioned `local` PersistentVolume |
| StorageClass | Non-default `signalforge-local-nvme` using `kubernetes.io/no-provisioner` |
| Binding mode | `WaitForFirstConsumer` |
| PV and PVC capacity | 30 GiB |
| Access mode | `ReadWriteOnce` |
| Reclaim policy | `Retain` |
| Node affinity | `kubernetes.io/hostname=forge-head` |
| Prometheus retention | 30 days or 24 GB, whichever is reached first |
| Prometheus workload | One-replica Deployment with `Recreate` strategy |
| User access | Existing ClusterIP Service and `kubectl port-forward` only |
| Routine backup | Weekly cold backup copied off `forge-head`; retain four |
| Recovery objectives | RPO of 7 days or less; RTO of 1 hour or less |

The 30 GiB Kubernetes allocation leaves filesystem headroom within the 32 GiB partition. The 24 GB Prometheus size limit targets approximately 80 percent of the advertised PV capacity, leaving space for the write-ahead log, memory-mapped head chunks, and temporary compaction overhead. The time and size limits operate together; the first limit reached removes the oldest eligible blocks.

The partition is the physical capacity boundary. The PV capacity advertises the resource to Kubernetes, while the Prometheus retention-size flag provides the application-level guardrail.

## Why this design

Prometheus uses a local on-disk time-series database and recommends a local POSIX-compatible filesystem. Its storage guidance explicitly does not support NFS for the TSDB and recommends reserving 15-20 percent of allocated storage when size-based retention is enabled.

Kubernetes `local` volumes represent a disk, partition, or directory attached to one node. They are statically provisioned, require PV node affinity, and allow the scheduler to understand that the consuming Pod must run on the storage node. Kubernetes recommends `WaitForFirstConsumer` for this volume type.

SignalForge has one Prometheus instance and one suitable NVMe device. A static local PV makes that physical relationship visible without adding a CSI system, storage controller, or network filesystem. The design deliberately accepts node-local availability because `forge-head` is already the cluster's only control plane; moving Prometheus alone to another node would not restore normal cluster operation after a head-node failure.

## Options considered

| Option | Decision | Reason |
|---|---|---|
| Static local PV on the head NVMe | Select | Direct ext4 storage, scheduler-aware node affinity, no additional controller, and minimal operational burden |
| Lightweight local-path provisioner | Defer | Simplifies repeated PVC creation but adds a controller and helper Pods without removing the node-local failure boundary; its documented volume-capacity limit is not enforced |
| NFS hosted by `forge-head` | Reject | Adds network-filesystem failure modes while preserving the same head-node dependency; Prometheus does not support NFS for its local TSDB |
| External NAS or NFS | Reject for the TSDB | Separates the hardware but still conflicts with Prometheus filesystem guidance |
| `hostPath` | Reject | Does not express node-aware persistent-storage scheduling as safely as a `local` PV in a multi-node cluster |
| Longhorn | Defer | Replication and CSI lifecycle management are disproportionate for one small workload and would place additional components and synchronous writes across Pi nodes whose current storage is primarily SD cards |
| Ceph or distributed OpenEBS storage | Reject now | Adds substantial platform and recovery complexity for the present requirement |
| Prometheus remote write | Future option | Appropriate if the project later requires off-cluster durability or longer-term metrics retention |

## Scheduling and binding

The PV must carry required node affinity for `forge-head`. Prometheus must not receive an independent hostname selector that duplicates the storage decision; the scheduler should derive placement from the selected PV.

The PVC should explicitly reference the named PV so that the dedicated volume cannot be claimed accidentally. The implementation must also confirm the live taints on `forge-head`. If its normal control-plane `NoSchedule` taint is present, Prometheus will receive one narrowly scoped matching toleration. The node must not be globally untainted.

The Prometheus Deployment will remain at one replica and use the `Recreate` strategy. This makes single-writer behavior explicit and avoids a rolling update attempting to run an old and new Prometheus Pod against the same `ReadWriteOnce` storage.

## Failure behavior

| Event | Expected behavior |
|---|---|
| Prometheus container or Pod replacement | The replacement mounts the same PVC; retained history survives and the WAL replays if needed |
| `forge-head` reboot | Prometheus remains unavailable until the node and NVMe return, then starts against the existing data |
| `forge-head` failure | The Prometheus Pod remains unschedulable instead of starting elsewhere with an empty database |
| NVMe or filesystem failure | Restore the newest valid off-node backup to repaired or replacement local storage, or start with an empty TSDB if history is expendable |
| Accidental PVC deletion | The `Retain` policy preserves the PV and underlying data for deliberate manual recovery |
| Mount missing at boot | The local-volume data path must be absent, causing the workload to fail rather than silently writing Prometheus data to the head-node SD card |

Persistence does not provide high availability or replication. That limitation is explicit and accepted for this lab.

## Filesystem and mount safeguards

Before destructive disk work, the implementation must identify the NVMe by model, serial number, size, device path, partition table, filesystems, mount state, and existing data. The operator must stop if any needed data or ambiguous device identity is found.

The dedicated partition will be formatted ext4 and mounted by UUID at `/mnt/signalforge-prometheus`. The Prometheus data subdirectory must be created only after the NVMe filesystem is mounted. It must not exist on the underlying root filesystem, because an otherwise valid path could allow fallback writes to the SD card when the NVMe mount is absent.

The initial 32 GiB partition leaves most of the 2 TB NVMe unallocated for later lab uses. Future capacity changes require expanding the partition and filesystem deliberately; changing only the PV capacity is not a physical resize mechanism.

## Backup and recovery strategy

The first backup method will be a cold, complete filesystem copy:

1. Scale the Prometheus Deployment to zero and verify that no Prometheus Pod remains.
2. Archive the complete TSDB directory from the mounted NVMe.
3. Copy the archive to a laptop or another device outside `forge-head`.
4. Generate and verify a SHA-256 checksum for the copied archive.
5. Retain the four newest weekly archives.
6. Take an additional backup before Prometheus upgrades, storage migration, or filesystem maintenance.
7. Scale Prometheus back to one and verify all three Restaurant API targets.

This approach avoids enabling the Prometheus administrative API solely for snapshots. If backup frequency or acceptable downtime later changes, native TSDB snapshots can be evaluated as a separate improvement.

A restore drill must use a temporary directory or replacement target and must not overwrite the active TSDB. The drill succeeds only when the archive checksum verifies, the files can be extracted, the expected TSDB structure is present, and `promtool tsdb analyze` can read the restored copy. A live restore remains a deliberate recovery operation performed only after the active data is protected.

## Migration and rollback

The current `emptyDir` data will not be migrated. The small amount of ephemeral history does not justify copying a live TSDB during the cutover. Milestone 026 will accept one intentional reset of at most the current 48-hour retention window and begin collecting on the empty NVMe-backed volume.

The rollback path is to restore the current `emptyDir` volume and 48-hour/750 MB retention arguments in the Deployment manifest. The retained PV and its files must remain untouched so the persistent data can be investigated or reused safely.

## Milestone 025 acceptance criteria

- [x] Compared static local PV, local-path provisioner, network storage, `hostPath`, distributed storage, and remote-write options.
- [x] Selected a dedicated ext4 partition on the head-node NVMe.
- [x] Defined the StorageClass, PV, PVC, node-affinity, workload-strategy, and access model.
- [x] Defined capacity and dual retention limits with compaction headroom.
- [x] Documented Pod, node, NVMe, deletion, and missing-mount failure behavior.
- [x] Defined off-node backup retention and recovery objectives.
- [x] Defined migration, restore-validation, and rollback expectations.
- [x] Preserved ClusterIP-only Prometheus access.
- [x] Made no storage or live-cluster changes.

## Milestone 026 implementation gate

Milestone 026 must not be considered complete until all of the following are verified:

- [ ] The NVMe model, serial number, existing partitions, filesystems, mounts, and absence of needed data are confirmed before partitioning.
- [ ] A dedicated 32 GiB ext4 partition is mounted by UUID at `/mnt/signalforge-prometheus`.
- [ ] `findmnt` proves that the Prometheus data path resides on the NVMe rather than the SD card.
- [ ] The data subdirectory exists only on the mounted NVMe, and a missing mount prevents fallback writes.
- [ ] `signalforge-local-nvme` exists, is non-default, uses `kubernetes.io/no-provisioner`, and uses `WaitForFirstConsumer`.
- [ ] The static 30 GiB PV uses `local`, `ReadWriteOnce`, `Retain`, and exact `forge-head` node affinity.
- [ ] The PVC is explicitly reserved for and bound to the intended PV before the existing Prometheus storage is replaced.
- [ ] The Prometheus container's runtime UID and GID are verified, and the NVMe data directory grants only the permissions required for that identity to write.
- [ ] The live head-node taint is inspected and only the necessary control-plane toleration is added.
- [ ] Prometheus remains one replica and uses the `Recreate` strategy.
- [ ] Retention is configured as 30 days and 24 GB.
- [ ] The Pod schedules on `forge-head` and mounts the expected filesystem.
- [ ] Deleting and recreating the Prometheus Pod preserves a known metric sample.
- [ ] Prometheus still reports three healthy Restaurant API targets.
- [ ] Prometheus remains reachable only through the ClusterIP Service and `kubectl port-forward`.
- [ ] An off-node cold backup and non-destructive restore-validation drill succeed.
- [ ] Rollback to the prior `emptyDir` manifest is documented and tested without deleting retained PV data.

## References

- [Prometheus storage](https://prometheus.io/docs/prometheus/latest/storage/)
- [Kubernetes local volumes](https://kubernetes.io/docs/concepts/storage/volumes/#local)
- [Kubernetes PersistentVolume reclaiming](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming)
- [Kubernetes PersistentVolume reservation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reserving-a-persistentvolume)
- [Rancher local-path provisioner](https://github.com/rancher/local-path-provisioner)
- [Longhorn architecture](https://longhorn.io/docs/1.12.1/concepts/)

## Next milestone

Milestone 026 should implement and validate the approved static local-PV design. Disk inspection and identity verification must occur before any partitioning command or cluster storage change.
