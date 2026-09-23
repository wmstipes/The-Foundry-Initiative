# Central logging: scoped design and preflight

## Goal and boundaries

Retain structured stdout from the two Service Pulse Pods across Pod replacement so operators can search `functional_check`, `checks_read`, and `probe_read` in Grafana. Start with namespace `forge-pulse` only. Do not turn on mesh injection, collect application Secrets, expose Loki publicly, or alter the existing Grafana and Prometheus volumes.

Proposed path: one Alloy instance in `forge-observability` discovers Pods only in `forge-pulse`, reads their logs via the Kubernetes API using a ServiceAccount with a Role limited to that namespace (`get/list/watch pods` and `get pods/log`), and writes to a private Loki ClusterIP. Loki runs as one process on `forge-head` with a dedicated persistent filesystem for chunks, index, WAL and compactor markers. Grafana gets a provisioned Loki datasource after the ingestion path is checked. Start with seven-day retention, a measured storage ceiling and alerts for usage. Avoid dynamic labels such as sample IDs and request IDs; retain those inside JSON messages for search.

## Storage gate before manifests

The existing Prometheus and Grafana PV paths are separate mounted filesystems. Grafana's 4 GiB filesystem was prepared on partition 2 of the Samsung NVMe and is already in use. A PV size is not a disk quota, and `Retain` does not back up data. **Do not create a Loki path under either existing mount or assume unallocated NVMe space.** First collect the following read-only inventory from the intended cluster context; review exact partition boundaries, free space, mount UUIDs, capacity and device health before choosing a dedicated disk extent and a bounded claim size. Preparation of a new partition or mount must have a separate reviewed procedure and backup gate.

```powershell
kubectl config current-context
kubectl get nodes -o wide
kubectl describe node forge-head
kubectl get pv,pvc -A -o wide
kubectl get pods -n forge-observability -o wide
kubectl get networkpolicy -A
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes wmstipes@192.168.243.110 'lsblk -o NAME,SIZE,FSTYPE,UUID,MOUNTPOINTS; df -hT /mnt/signalforge-prometheus /mnt/signalforge-grafana; sudo -n sfdisk --dump /dev/nvme0n1; sudo -n sfdisk --list-free /dev/nvme0n1; sudo -n nvme smart-log /dev/nvme0n1'
```

Confirm the actual device path before running the final SSH line; `/dev/nvme0n1` is only the historical Samsung device identifier. The SSH destination is the one in the existing Grafana preflight helper; adjust it if that trusted inventory changed. Capture outputs without sharing credentials or Secret values. Compare with `k8s/grafana/README.md` and `k8s/prometheus/README.md`. If there is no suitable free extent, choose an alternate storage backend before drafting an apply procedure.

## Deployment and acceptance gates

1. Pin reviewed Loki and Alloy image index digests and verify ARM64 manifests, release dates and running image IDs. Validate retention configuration with a persistent compactor directory and a 24-hour TSDB index period. Set modest CPU and memory requests/limits and restricted security contexts. Review namespace-scoped permissions and API load for one collector.
2. Validate configuration locally, then server-side dry-run and `kubectl diff` each resource. Start Loki first and verify `/ready`, persistent volume binding, and no restart loop. Start Alloy only after Loki is ready. Grafana datasource is last.
3. Find a Pulse `sampleId` in its live Pod log and in Grafana Explore. Record the observed UTC time and browser-local time, Pod name, and JSON result. Delete **only one** Pulse Pod after a controlled window; find an earlier sample from that Pod in Loki after replacement and a new sample from the replacement. This tests actual retention across Pod lifecycle, not just collector readiness.
4. Verify seven-day retention when old data exists and monitor disk usage and ingestion errors. Back up Loki data to a separate location and test isolated restore before treating this as durable history. A single local Loki instance and one collector are lab-scale components and have no high availability.

## Rollback

If ingestion fails, remove the Alloy Deployment first. Remove only the new Loki workload and datasource after preserving logs needed for diagnosis. Keep the dedicated PV/filesystem until its contents and any backup obligations are reviewed. Leave Prometheus, Grafana, Pulse and the Restaurant API intact.

Official references: [Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/), [filesystem storage](https://grafana.com/docs/loki/latest/operations/storage/filesystem/), [Alloy Kubernetes log source](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/), and [Alloy discovery](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.kubernetes/).
