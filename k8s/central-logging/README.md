# Service Pulse central logging

The [Loki recovery candidate](../../docs/milestones/loki-recovery-candidate.md)
adds source-only backup and isolated restore tooling after the observed
probe-Pod replacement check. Live `--execute` paths require separate review
and authorization; the rollout record below remains historical.

This directory records the accepted lab rollout; it is not an apply-all bundle. It uses one local Loki 3.7.0 StatefulSet and one Alloy v1.17.0 Deployment. Alloy discovers `forge-pulse` Pod logs using namespace-scoped RBAC, and Loki stores them on a dedicated 8 GiB NVMe partition. No Istio injection changes. The data remains on `forge-head` and needs an off-node backup and restore exercise before being called durable. See [inventory and storage gate](../../docs/milestones/central-logging-preflight.md).

| Image | Release date (UTC) | OCI index | Linux ARM64 child |
| --- | --- | --- | --- |
| `grafana/loki:3.7.0` | 2026-03-26 | `sha256:c316b7c7589a5eeca843b6926c7446149d18300b79ac8538dc4ae063bc478da2` | `sha256:a7280d594e8d49e9d123a06a4baeea95f3a7d1d4e8a7ff134b4f3d2c8d9a8e7d` |
| `grafana/alloy:v1.17.0` | 2026-06-12 | `sha256:41c41849989b7e054ccbadc17938ee1e5592fe26bfbc56ef3ffc109c0b0b2739` | `sha256:8df47d78640baa0be93b55fd5d2122e27ba244a5e8846cf9e36b554729dabf79` |

Identities were checked against Docker Hub's tag API and the [Loki release](https://github.com/grafana/loki/releases/tag/v3.7.0) and [Alloy release](https://github.com/grafana/alloy/releases/tag/v1.17.0) on 2026-09-23. Recheck tag and digest metadata at deployment time. These checks establish registry metadata, not runtime compatibility or vulnerability status.

Local validation on 2026-09-23: the Loki v3.7.0 Linux AMD64 release executable returned success for `-verify-config` on the ConfigMap's `config.yaml`, and the Alloy v1.17.0 Linux AMD64 release executable returned success for `validate` on `config.alloy`. YAML parsed, the proposed sector bounds were checked, and the repository manifest validator passed. These local checks alone do not prove ARM64 startup, Pod admission, mounted storage, collection, retention or Grafana queries; subsequent live results below establish startup, collection, and querying. Retention remains unverified.

## Storage preparation, separate gate

**Completed and independently verified 2026-09-23. Do not rerun the storage preparation script.** The operator reported `LOKI_FILESYSTEM_UUID=93a19402-4a5b-4689-aed7-f1841c2cb53b` and `HOST_EVIDENCE=/var/tmp/signalforge-loki-storage.8EDDMf` after the guarded partition/mount procedure. A subsequent independent read showed `/dev/nvme0n1p3` mounted read/write with the expected UUID, `/data` owner `10001:10001` mode `750`, and 7.4 GiB available. The Prometheus and Grafana mounts remained present with their prior UUIDs. The read-only verification commands are retained here for future checks:

```bash
findmnt -n -o SOURCE,UUID,FSTYPE,OPTIONS --mountpoint /mnt/signalforge-loki
lsblk -o NAME,SIZE,FSTYPE,UUID,MOUNTPOINTS /dev/nvme0n1
stat -c '%u:%g %a %n' /mnt/signalforge-loki/data
df -hT /mnt/signalforge-loki
```

Expect `/dev/nvme0n1p3`, ext4 UUID `93a19402-4a5b-4689-aed7-f1841c2cb53b`, owner `10001:10001`, and an approximately 8 GiB filesystem. The preparation procedure below is retained as an audit record, not a new instruction to run it.

The operator has chosen to proceed without a fresh off-node backup at this stage; Prometheus currently reports 27 MiB used and Grafana 2.6 MiB used. This choice does not make their existing data expendable: the storage script still verifies both partitions and active mounts and saves the table and fstab on the head's SD card before the write. A failed NVMe requiring replacement would make that on-node evidence insufficient for data recovery. The optional off-node path remains available. The previously accepted Prometheus archive is `prometheus-tsdb-20260910-150206Z.tar.gz` with SHA-256 `68e00637d6fd05db21bc8e5dbefa7bbb7d65a7548dd3de0eec5c2faae574dc24`.

For **optional off-node partition-table evidence**, in an interactive SSH session as `wmstipes@192.168.243.110`, save a fresh read-only table dump in your home directory:

```bash
sudo sfdisk --dump /dev/nvme0n1 > ~/loki-nvme-before.sfdisk
sha256sum ~/loki-nvme-before.sfdisk
```

On the Windows NUC, copy that dump off-node, then confirm its hash is identical to the one printed on the head:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SignalForge-Backups\storage" | Out-Null
scp wmstipes@192.168.243.110:~/loki-nvme-before.sfdisk "$env:USERPROFILE\SignalForge-Backups\storage\loki-nvme-before.sfdisk"
Get-FileHash -LiteralPath "$env:USERPROFILE\SignalForge-Backups\storage\loki-nvme-before.sfdisk" -Algorithm SHA256
```

Copy the reviewed storage script from the same Git revision to the head, then compare its SHA-256 on both machines before running it:

```powershell
Get-FileHash -LiteralPath .\scripts\prepare-loki-storage.sh -Algorithm SHA256
scp .\scripts\prepare-loki-storage.sh wmstipes@192.168.243.110:~/prepare-loki-storage.sh
```

```bash
sha256sum ~/prepare-loki-storage.sh
```

Run its plan on the head. It checks the serial, model, sector size, both live filesystem UUIDs, exact GPT layout and partition GUIDs, and NVMe warning/spare/error baseline, then uses `sfdisk --no-act`. It writes nothing:

```bash
sudo bash prepare-loki-storage.sh --plan
```

The **disk write** has two explicit modes: `--prepare <verified-off-node-table-sha256>` if using the optional off-node copy, or `--prepare-without-offnode-backup` for the operator's current choice. Neither is the default. Both verify the live partition layout and drive identity, save and hash a fresh table dump plus fstab on the head's SD card, preview the append, and then append only partition 3 (start `75499520`, length `16777216`, end `92276735`). They verify old partition records did not change, check for signatures before formatting, create a new ext4 filesystem, mount by UUID and check that Loki UID 10001 can write. Review the `--plan` output before invoking either write mode. If the script stops after a write, inspect the saved host evidence; do not rerun or format again. Record the printed `LOKI_FILESYSTEM_UUID` and verify it against `findmnt` and `lsblk` before Kubernetes apply.

## Phased Kubernetes review and rollout

Do not apply this directory wholesale. The filesystem must exist at `/mnt/signalforge-loki/data` with UUID and UID/GID `10001:10001` verified first. From PowerShell, check the cluster context, Node status and allocatable capacity, the `forge-pulse` namespace, the storage class, Pod Security admission, and that no conflicting Loki PV/PVC exists. Confirm the two image identities again. Use `kubectl apply --dry-run=server -f <path>` and `kubectl diff -f <path>` **for each file** before each apply. The external `diff.exe` on the Windows PATH is required for `kubectl diff`.

Storage preview accepted 2026-09-23: context `kubernetes-admin@kubernetes`; `loki-local-nvme` PV and `loki-data` PVC were absent. Server-side dry-run proposed creation of both, and the diff showed only a new 8 GiB `ReadWriteOnce` local PV at `/mnt/signalforge-loki/data`, reserved for `forge-observability/loki-data`, node-affined to `forge-head`, and a matching PVC. The StorageClass uses `WaitForFirstConsumer`, so an unapplied dry-run appears `Pending` and the live PVC may remain `Pending` until the Loki StatefulSet Pod is scheduled. Do not interpret that alone as a failed binding.

The operator subsequently reported `kubectl apply -f loki-storage.yaml` returned `unchanged` for both objects (they already existed at the time of that command). A live read showed PV `loki-local-nvme` and PVC `forge-observability/loki-data` **Bound** to each other at 8 GiB, `RWO`, `signalforge-local-nvme`, PV reclaim policy `Retain`.

Loki startup accepted 2026-09-23: the ConfigMap, ingress NetworkPolicy, and Service passed server-side dry-run and diff before apply. The StatefulSet also passed server-side dry-run and diff, then its rollout completed. `loki-0` was 1/1 Ready and Running on `forge-head` with zero restarts; the mounted `loki-data` PVC remained Bound and the `loki` Service had an EndpointSlice on port 3100 pointing to its Pod IP `10.244.253.240`. `kubectl describe pod` reported startup probe failures (connection refused and HTTP 503) followed by readiness. In a subsequent five-minute, 80-line log window, one `empty ring` error appeared at startup and no later errors were shown. This establishes a ready single-instance Loki, but ingestion, query, and retention still require separate verification.

Alloy collection and Loki query accepted 2026-09-23: the Alloy RBAC, ConfigMap, and Deployment passed server-side dry-run and diff before apply. The first Pod exited because the Deployment used unsupported `--disable-support-bundle`; the manifest was corrected to `--server.http.disable-support-bundle=true`, independently previewed and applied by the operator. The replacement Pod was 1/1 Ready with zero restarts, and Alloy opened log streams for both Service Pulse Pods. A Loki `query_range` result returned a `functional_check` line for `service-pulse-probe`, labeled `namespace=forge-pulse`, `container=service-pulse-probe`, with `sampleId=8f9329958c784ef0b795cd1fa8b11732`. This established a queryable central log at the collection gate.

Grafana Explore verified 2026-09-23: the operator confirmed that the existing Prometheus source differs from the newly rendered ConfigMap only by CRLF/LF line endings. The rendered ConfigMap added `loki.yaml`, was applied, and Grafana rolled out successfully. A browser screenshot shows `SignalForge Loki` in Explore returning recent `functional_check` lines from `service-pulse-probe` under the expected LogQL selector. The selected query displayed 120 lines; displayed local time corresponds to the embedded UTC timestamp. On 2026-09-24, the Grafana regression script completed successfully after restoring the localhost port-forward: Grafana 13.2.1 reported its database healthy, both existing dashboards' panel queries were accepted, and three Restaurant API targets were healthy. Retention and restore checks are still pending.

Probe Pod replacement check passed 2026-09-24: the operator recorded `sampleId=bfa2350926ed44d181678c02a4439ec0` at 14:44:08Z before replacing the probe. Grafana Explore returned that exact log after the replacement, while Kubernetes showed only the replacement Pod `service-pulse-probe-6c7f9c9cc9-klrsj` (1/1 Ready, zero restarts). A separate later query showed a fresh successful check at 14:51:44Z with a different sample ID. The observed result establishes that Loki retained and served an old probe log after its source Pod was removed. It does not establish that Loki's own data survives a restart, that seven-day retention is enforced, or that an off-node restore works.

On Windows where direct PowerShell script execution is disabled, run the existing Grafana regression script in a separate process with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-grafana.ps1` from the repository root while the Grafana port-forward is active. This does not change the persistent execution policy. Supply Grafana credentials only at its interactive prompt and omit them from shared output.

The numbered procedure below records the original staged deployment and can guide a reviewed rebuild. Its apply and Pod replacement steps have already been completed for this cluster; do not rerun them as routine follow-up.

1. Apply `loki-storage.yaml`, then inspect that both resources have the intended immutable specs; binding can wait for the first consumer. Apply `loki-config.yaml`, `loki-networkpolicy.yaml`, `loki-service.yaml`, and `loki-statefulset.yaml` individually. A policy admits TCP/3100 only from the `pulse-alloy` and `grafana` Pods in the same namespace. Confirm the PV/PVC bind after the Loki Pod schedules. Wait for `kubectl rollout status statefulset/loki -n forge-observability --timeout=180s` and check `/ready` by port-forward. A Ready Pod alone does not establish retention or ingestion.
2. Apply `alloy-rbac.yaml`, `alloy-config.yaml`, and `alloy-deployment.yaml` separately. Confirm `kubectl auth can-i get pods/log -n forge-pulse --as=system:serviceaccount:forge-observability:pulse-alloy` is yes and the equivalent in `forge-restaurant` is no. Observe its logs and target health before trusting ingestion.
3. Find a Pulse `sampleId` from a `functional_check` record through Loki's API before changing Grafana. Existing Grafana's `grafana-datasources` ConfigMap is generated from `k8s/grafana/provisioning/datasources`; update it using the existing Grafana helper after review so it includes `loki.yaml`, then restart/verify Grafana. Check Explore with `{namespace="forge-pulse",container="service-pulse-probe"} |= "functional_check"` and confirm the same sample ID as a live Pod log.
4. Replace only one Pulse Pod after recording its sample ID. Find that old ID after replacement, alongside fresh samples from the new Pod. Check WAL/compactor paths on the PVC, disk usage, errors and Pod restarts. Create an off-node Loki backup and isolated restore exercise before relying on the seven-day policy.

## Recovery

If collection fails, scale down `pulse-alloy` first and inspect errors. Retain Loki PVC/PV and partition evidence for diagnosis; deleting a workload does not delete its retained local volume. If Grafana provisioning fails, restore its previously captured ConfigMap and restart Grafana without modifying Prometheus data. No step should delete an existing Prometheus or Grafana resource.
