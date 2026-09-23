# Central logging: scoped design and preflight

## Goal and boundaries

Retain structured stdout from the two Service Pulse Pods across Pod replacement so operators can search `functional_check`, `checks_read`, and `probe_read` in Grafana. Start with namespace `forge-pulse` only. Do not turn on mesh injection, collect application Secrets, expose Loki publicly, or alter the existing Grafana and Prometheus volumes.

Proposed path: one Alloy instance in `forge-observability` discovers Pods only in `forge-pulse`, reads their logs via the Kubernetes API using a ServiceAccount with a Role limited to that namespace (`get/list/watch pods` and `get pods/log`), and writes to a private Loki ClusterIP. Loki runs as one process on `forge-head` with a dedicated persistent filesystem for chunks, index, WAL and compactor markers. Grafana gets a provisioned Loki datasource after the ingestion path is checked. Start with seven-day retention, a measured storage ceiling and alerts for usage. Avoid dynamic labels such as sample IDs and request IDs; retain those inside JSON messages for search.

## Storage gate before apply

The existing Prometheus and Grafana PV paths are separate mounted filesystems. Grafana's 4 GiB filesystem was prepared on partition 2 of the Samsung NVMe and is already in use. A PV size is not a disk quota, and `Retain` does not back up data. **Do not create a Loki path under either existing mount or assume unallocated NVMe space.** First collect the following read-only inventory from the intended cluster context; review exact partition boundaries, free space, mount UUIDs, capacity and device health before choosing a dedicated disk extent and a bounded claim size. Preparation of a new partition or mount must have a separate reviewed procedure and backup gate.

### Operator inventory, 2026-09-23

The operator ran the read-only host checks interactively over SSH as `wmstipes` because the older Grafana preflight script uses `BatchMode=yes` and cannot prompt for a password. The Kubernetes portion of that script succeeded; its SSH portion stopped at authentication. The direct host output established:

| Item | Observed value |
| --- | --- |
| Device | `/dev/nvme0n1`, GPT ID `FDF2C7FC-C23E-4147-93B5-B53D85A08F78`, 512-byte sectors, last usable LBA `1000215182` |
| Prometheus partition | `p1` start `2048`, length `67108864`, filesystem UUID `4f2feee5-72a7-4f32-a351-b4253c4a0854`, mounted at `/mnt/signalforge-prometheus` |
| Grafana partition | `p2` start `67110912`, length `8388608`, filesystem UUID `a506c674-127a-46da-9c7d-d158b6d1bb75`, mounted at `/mnt/signalforge-grafana` |
| Unallocated extent | sectors `75499520`–`1000215182`, 440.94 GiB |
| Drive health | critical warning `0`, spare `99%`, used `2%`, media errors `215` (same count recorded at the Grafana storage gate), temperature `306 K` |
| Drive identity | `Samsung SSD 950 PRO 512GB`, serial `S2GMNCAGB06236R`, confirmed by operator after the disk inventory |

**Proposed Loki allocation for review:** a new 8 GiB partition `p3` beginning at sector `75499520`, length `16777216` sectors, ending at `92276735`. The next sector, `92276736`, remains unallocated. This allocates less than two percent of the reported unused extent. Mount it by its newly generated filesystem UUID at `/mnt/signalforge-loki`, with a dedicated `/mnt/signalforge-loki/data` directory for Loki UID/GID `10001:10001`. A static 8 GiB PV and reserved PVC would reference that directory, bind only on `forge-head`, and use `Retain`. The partition, rather than the PV's nominal capacity, would enforce the actual filesystem ceiling. Seven-day retention is a policy target; disk alerts and a tested backup are still required. **This is an allocation proposal, not a command to partition the disk.**

Before any write, verify device model/serial, sector size, mounted UUIDs, exact `p1` and `p2` boundaries and PARTUUIDs, free extent, NVMe warnings/spare/media errors, and absence of `p3`, a Loki mount or fstab entry. An append-only `sfdisk --no-act` preview and a per-partition kernel update must precede filesystem creation. The operator chose to proceed without a fresh off-node backup because current application data use is small. The dedicated Loki helper therefore permits `--prepare-without-offnode-backup`, but first saves and verifies the partition table and fstab on the head's SD card. An optional `--prepare` mode still checks a verified off-node table dump's SHA-256. Neither mode backs up application data. After a partial write, stop for review; never rerun formatting automatically. The existing Grafana storage preparation helper is **not** safe to run again for Loki.

```powershell
kubectl config current-context
kubectl get nodes -o wide
kubectl describe node forge-head
kubectl get pv,pvc -A -o wide
kubectl get pods -n forge-observability -o wide
kubectl get networkpolicy -A
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes wmstipes@192.168.243.110 'lsblk -o NAME,SIZE,FSTYPE,UUID,MOUNTPOINTS; df -hT /mnt/signalforge-prometheus /mnt/signalforge-grafana; sudo -n sfdisk --dump /dev/nvme0n1; sudo -n sfdisk --list-free /dev/nvme0n1; sudo -n nvme smart-log /dev/nvme0n1'
```

Confirm the actual device path before running the final SSH line; `/dev/nvme0n1` is only the historical Samsung device identifier. The SSH destination is the one in the existing Grafana preflight helper; adjust it if that trusted inventory changed. The commands shown use `BatchMode=yes` and `sudo -n`, so they require preconfigured passwordless SSH and sudo. When either prompts for a password, use an interactive SSH session and run the read-only commands individually; do not weaken host-key verification or paste credentials into output. Compare with `k8s/grafana/README.md` and `k8s/prometheus/README.md`. If there is no suitable free extent, choose an alternate storage backend before drafting an apply procedure.

## Deployment and acceptance gates

1. Recheck the reviewed Loki and Alloy image index digests and ARM64 manifests against the registry; record running image IDs. Validate retention configuration with a persistent compactor directory and a 24-hour TSDB index period. Review namespace-scoped permissions and API load for one collector. The candidate manifests and image identities are in `k8s/central-logging/README.md`.
2. Validate configuration locally, then server-side dry-run and `kubectl diff` each resource. Start Loki first and verify `/ready`, persistent volume binding, and no restart loop. Start Alloy only after Loki is ready. Grafana datasource is last.
3. Find a Pulse `sampleId` in its live Pod log and in Grafana Explore. Record the observed UTC time and browser-local time, Pod name, and JSON result. Delete **only one** Pulse Pod after a controlled window; find an earlier sample from that Pod in Loki after replacement and a new sample from the replacement. This tests actual retention across Pod lifecycle, not just collector readiness.
4. Verify seven-day retention when old data exists and monitor disk usage and ingestion errors. Back up Loki data to a separate location and test isolated restore before treating this as durable history. A single local Loki instance and one collector are lab-scale components and have no high availability.

## Rollback

If ingestion fails, remove the Alloy Deployment first. Remove only the new Loki workload and datasource after preserving logs needed for diagnosis. Keep the dedicated PV/filesystem until its contents and any backup obligations are reviewed. Leave Prometheus, Grafana, Pulse and the Restaurant API intact.

Official references: [Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/), [filesystem storage](https://grafana.com/docs/loki/latest/operations/storage/filesystem/), [Alloy Kubernetes log source](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/), and [Alloy discovery](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.kubernetes/).
