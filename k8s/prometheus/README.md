# SignalForge Lightweight Prometheus

These manifests deploy a single Prometheus server for the Restaurant API.

## Scope

- Namespace: `forge-observability`
- Prometheus image: `prom/prometheus:v3.13.2`
- One Prometheus replica
- Pod discovery limited to `forge-restaurant`
- Scrape target limited to Restaurant API containers on the named `http` port
- Scrape interval: 30 seconds
- Retention time: 30 days
- Retention size: 24 GB
- Storage: static 30 GiB local PV on the `forge-head` NVMe
- Access: `kubectl port-forward` only

No Grafana, Alertmanager, node-exporter, kube-state-metrics, Prometheus Operator, dynamic provisioner, or distributed storage platform is installed.

## Resources

- `namespace.yaml` creates `forge-observability`.
- `prometheus-service-account.yaml` provides the Prometheus workload identity.
- `restaurant-pod-reader-role.yaml` grants read-only Pod discovery in `forge-restaurant`.
- `restaurant-pod-reader-role-binding.yaml` binds that Role to the Prometheus ServiceAccount.
- `prometheus-config.yaml` defines the Restaurant API scrape job.
- `prometheus-storage-class.yaml` defines the non-default, no-provisioner local StorageClass.
- `prometheus-local-pv.yaml` represents `/mnt/signalforge-prometheus/data` on `forge-head` and retains its data after claim release.
- `prometheus-data-pvc.yaml` reserves the named local PV for Prometheus.
- `prometheus-storage-preflight-pod.yaml` is a temporary first consumer that binds and write-tests the PVC before cutover.
- `prometheus-backup-pod.yaml` mounts the stopped TSDB read-only while a cold archive streams off-node.
- `prometheus-restore-validation-pod.yaml` mounts only an isolated restored copy for `promtool` validation.
- `prometheus-deployment.yaml` mounts the PVC and runs Prometheus with bounded resources and retention.
- `prometheus-service.yaml` provides an internal-only ClusterIP.

## Host prerequisite

The storage manifests assume that `forge-head` already has the dedicated ext4 filesystem mounted at `/mnt/signalforge-prometheus` and that its `data` directory is writable only by the Prometheus runtime identity (`65534:65534`). The data directory must not exist on the underlying root filesystem when the NVMe is unmounted.

For this cluster, the verified filesystem is:

```text
Device: /dev/nvme0n1p1
Model: Samsung SSD 950 PRO 512GB
Serial: S2GMNCAGB06236R
Filesystem UUID: 4f2feee5-72a7-4f32-a351-b4253c4a0854
Mount: /mnt/signalforge-prometheus
Data path: /mnt/signalforge-prometheus/data
```

Host partitioning and formatting are intentionally not automated by the deployment helper.

Because the StorageClass uses `WaitForFirstConsumer`, the helper briefly creates the preflight Pod before applying the new Deployment. PV node affinity schedules that Pod on `forge-head`; it writes and removes a marker as UID/GID 65534, then the helper removes it. A binding, scheduling, mount, or write failure stops the operation while the existing `emptyDir`-backed Prometheus Deployment is still unchanged.

## Deploy

From the repository root on the laptop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-deploy
```

## Check collection

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-storage
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-targets
```

The target query should return `3` while all three Restaurant API Pods are ready.

After the initial deployment, prove that a known sample survives deliberate Pod replacement:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-persistence
```

This command deletes only the current Prometheus Pod. The Deployment recreates it against the same retained PVC, and the test queries a sample recorded before replacement at its original timestamp.

## Back up and validate recovery

Create a cold backup on the Windows operator laptop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-backup-ready
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-backup
```

The readiness command confirms that Prometheus has at least one compacted block. The backup command enforces that gate again before downtime, scales Prometheus to zero, waits for graceful shutdown, mounts the PVC read-only in a temporary Pod, and uses binary-safe Windows redirection to stream the compressed archive directly to `%USERPROFILE%\SignalForge-Backups\prometheus`. It records SHA-256, retains four archives, scales Prometheus back to one, and verifies three healthy targets.

Validate the newest retained archive without overwriting the active TSDB:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-restore-test
```

The restore check verifies the laptop copy's checksum, refuses to overwrite an existing validation directory, creates `/mnt/signalforge-prometheus/restore-validation`, streams the archive into it, and runs `promtool tsdb list` and `promtool tsdb analyze` against that isolated copy. It never mounts `/mnt/signalforge-prometheus/data` and removes only the temporary restored copy afterward. The command may prompt for the `forge-head` sudo password.

The first compacted block can take roughly three hours to appear. Use `metrics-backup-ready` rather than relying on elapsed time before the first acceptance backup.

## Open the Prometheus UI

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-ui
```

Then open `http://localhost:9090`.

## Persistence and availability

Replacing the Prometheus Pod preserves history on the local PV. The volume is node-local rather than replicated, so Prometheus remains unavailable while `forge-head` or its NVMe is unavailable.

The PV and StorageClass both use `Retain`. Deleting a claim does not authorize deletion of `/mnt/signalforge-prometheus/data`; recovery and reuse are deliberate operator actions.
