# Milestone 027 Lightweight Grafana Planning

Date: 2026-09-10

Status: Complete with operator agreement

Project: The Foundry Initiative / SignalForge

Repository baseline: `main`, `653ffa6f730e61e4615d5e7fc188eb41c089df18`

## Recommendation

Deploy one Grafana OSS instance in `forge-observability`, managed with plain Kubernetes manifests and file provisioning. Begin with two small dashboards using the existing Restaurant API metrics. Keep browser access through a localhost-bound `kubectl port-forward` and persist Grafana's SQLite database on a separate small NVMe filesystem.

This document defines the accepted design and the implementation gate. The operator agreed to this design on 2026-09-10, completing Milestone 027 planning. Grafana has not been deployed. A subsequent implementation milestone should collect the live acceptance evidence.

## Repository review

The local repository was clean on `main` at the supplied commit. The review covered the README, contribution conventions, architecture, project status, Milestones 021 and 025â€“026, application instrumentation, PromQL baseline, Prometheus manifests, and manifest-validator structure. No cluster commands were run during this planning review; current runtime findings below are recorded Milestone 026 evidence and operator-provided state.

The repository already favors versioned images, plain manifests, PowerShell helpers, restricted RBAC, and small milestones. The application publishes request counters and duration histograms with `method`, `path`, `status`, and `traffic` labels, plus version metadata and an analyze-feature gauge. Prometheus adds `namespace`, `pod`, and `node` labels through Pod discovery.

The collector has exactly one configured job, `restaurant-api`, scraped every 30 seconds. It does not scrape itself. Its Service is `prometheus`, port `9090`, in `forge-observability`. This supports application and scrape-quality dashboards immediately. It does not support historical node CPU, node memory, disk capacity, Kubernetes desired replica counts, or Prometheus TSDB internals without additional collection.

Metrics Server continues to support `kubectl top` with verified kubelet TLS. It should not become a Grafana data source; upstream explicitly distinguishes it from a monitoring pipeline. [Metrics Server guidance](https://kubernetes-sigs.github.io/metrics-server/)

Milestone 026's limitations remain: weekly Prometheus backups are manual; full service-restoration RTO is unmeasured; the temporary rollback Pod became Ready but its target check was blocked by PowerShell execution policy. The restored persistent collector passed final checks with six blocks and three healthy targets.

## Deployment and resource design

| Item | Proposed value |
|---|---|
| Workload | `Deployment/grafana`, one replica, `Recreate`, three retained revisions |
| Namespace | Existing `forge-observability` |
| Image | Official `grafana/grafana` OSS image; exact stable patch tag and digest pinned before implementation |
| Architecture | Verify the selected image contains `linux/arm64`; record its runtime UID and GID |
| Resources | Request `100m` CPU and `512Mi` memory; limit `1000m` CPU and `1Gi` memory |
| Placement | `forge-head`, derived from the local PV's required hostname node affinity |
| Toleration | Only the existing control-plane `NoSchedule` taint if still present |
| Service | `ClusterIP/grafana`, port `3000`; no NodePort, Ingress, host port, or host network |
| Runtime data | `/var/lib/grafana` on `grafana-data` PVC |
| Probes | Startup and readiness at `/api/health`; conservative TCP liveness on port `3000` |
| Extensions | Built-in Prometheus data source and built-in panels only |

The resource values are initial lab budgets, not measured requirements. Grafana recommends at least 512 MB memory and one CPU core. The lower CPU request assumes one operator and small dashboards, while the limit allows one core for startup and queries. Confirm head-node allocatable resources and existing requests before admission. [Grafana installation requirements](https://grafana.com/docs/grafana/latest/setup-grafana/installation/)

Proposed probe starting values: startup every 10 seconds with 30 failures allowed; readiness every 10 seconds with a 5-second timeout and three failures; TCP liveness every 20 seconds with a 5-second timeout and six failures. Startup gates the other probes. TCP liveness avoids a database-health failure causing continuous restarts; acceptance must also check login and queries.

Use a dedicated ServiceAccount with `automountServiceAccountToken: false` and no Kubernetes API permissions. Run non-root using the selected image's verified identity, drop all capabilities, disable privilege escalation, and use `RuntimeDefault` seccomp. Use a read-only container root filesystem if the selected image passes startup with explicit writable mounts for data and temporary files. Log to stdout with runtime log rotation; do not add a log collector.

Choose the exact supported stable patch release after reviewing its security notices, release notes, ARM64 manifest, and provisioning compatibility immediately before implementation. Do not commit `latest` or infer a compatible version from a dashboard export. Grafana does not need to match Prometheus's version number.

Plain manifests fit the established repository and expose all resources for review. A standalone Helm chart remains a reasonable future option if configuration grows. `kube-prometheus-stack`, the Grafana Operator, database servers, sidecars, Git Sync, image rendering, and third-party plugins add unnecessary components for this scope. Alert rules and notification integrations are deferred.

## Persistence and failure boundaries

Recommend a new dedicated **4 GiB ext4 partition** in verified unused space on the head NVMe, advertising a **3 GiB local PV**. Proposed names are `grafana-local-nvme` and `grafana-data`; proposed mount and data paths are `/mnt/signalforge-grafana` and `/mnt/signalforge-grafana/data`.

Reuse the existing non-default `signalforge-local-nvme` StorageClass with `kubernetes.io/no-provisioner` and `WaitForFirstConsumer`. Reserve the PV for `forge-observability/grafana-data`, explicitly name the PV in the PVC, use `ReadWriteOnce` and `Retain`, and require `kubernetes.io/hostname=forge-head`. Kubernetes documents the node affinity and delayed-binding model for local volumes. [Kubernetes local volumes](https://kubernetes.io/docs/concepts/storage/volumes/#local)

Do not share the Prometheus PVC, put Grafana under the Prometheus data directory, or spend the remaining space within its dedicated 32 GiB partition. The advertised 30 GiB PV and 24 GB retention limit leave headroom needed for Prometheus operations. Grafana's separate filesystem provides capacity isolation, although both services still share one physical drive.

The new partition is a proposal, not an observed available allocation. Before any disk work, verify the Samsung SSD 950 PRO identity, serial `S2GMNCAGB06236R`, current health, partitions, free extents, mounts, and backups. Capture the current partition table. Preserve the existing partition's exact boundaries and filesystem UUID. Never repeat the earlier whole-disk erase. If unused space or drive health cannot be established, stop host preparation and revise the storage design.

Mount by UUID, set ownership to the verified Grafana identity, and prove the data directory does not fall back to the SD-backed filesystem when the mount is absent. Use an unmounted parent without a `data` child and a mount-identity preflight before initial deployment and maintenance. Ensure the filesystem mounts before the workload can start. A missing mount must block startup rather than silently create a new database.

The 3 GiB PV capacity is Kubernetes accounting, not a filesystem quota. The 4 GiB partition is the physical boundary. Check filesystem usage during weekly operations; investigate at 70 percent used and act before 85 percent. Grafana stores application state, not the Prometheus time series. No additional metrics-retention policy belongs in Grafana. SQLite is the default embedded database. [Grafana container storage](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/)

Pod replacement should preserve accounts, preferences, and database state. Node or NVMe failure makes Grafana unavailable until recovery. `Recreate` expresses the single-writer intent, but RWO does not itself prevent two Pods on the same node from mounting the claim: backup and recovery procedures must ensure the server is stopped. Retain protects against automatic data reclamation, not disk failure or operator deletion.

An ephemeral Grafana is simpler to place but would reset login and user state on Pod replacement. It remains an explicit fallback only if the operator chooses reproducible dashboards over persistent accounts. A separate database or replicated storage is disproportionate to this lab.

## Provisioning and source of truth

Keep the configuration in a future `k8s/grafana` directory: Deployment, ServiceAccount, Service, PV/PVC, nonsecret Grafana settings, data-source provisioning, dashboard-provider provisioning, and two dashboard JSON files. Document host preparation and recovery in its README. Add Grafana-specific checks to the existing manifest validator and PowerShell helpers after design agreement. Do not assume the current validator covers newly introduced Grafana resources.

Use ordinary ConfigMap directory mounts, not `subPath` mounts for files intended to refresh. Generate ConfigMaps deterministically from the version-controlled source files in the deployment helper; review the rendered resources before applying. Keep each object below Kubernetes's 1 MiB ConfigMap limit. No watching sidecar or cluster-wide RBAC is required.

Proposed data source:

```yaml
apiVersion: 1
datasources:
  - name: SignalForge Prometheus
    uid: signalforge-prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.forge-observability.svc.cluster.local:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 30s
      httpMethod: POST
```

Confirm the live cluster DNS suffix before using the fully qualified name. Grafana queries Prometheus from inside the cluster; `localhost:9090` would point at Grafana's own Pod.

Use folder `SignalForge` with stable folder UID `signalforge`, provider type `file`, `updateIntervalSeconds: 30`, `allowUiUpdates: false`, `disableDeletion: false`, and source path `/etc/grafana/dashboards`. Give dashboards stable UIDs `signalforge-restaurant-overview` and `signalforge-scrape-diagnostics`. Export changes to JSON, review and commit them, then redeploy; a browser edit is not the source of truth. The deletion setting makes removal from Git remove a dashboard from provisioning, so deletions require review. Grafana documents polling and the precedence of provisioned files over UI edits. [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)

Dashboard JSON updates may follow ConfigMap propagation and polling. Settings and data-source changes get a deliberate `Recreate` rollout; do not assume hot reload. Provisioning-file and dashboard-format compatibility must be tested against the pinned version.

## Credentials and access

Create an operator-managed Kubernetes Secret `grafana-admin` with a unique bootstrap admin username, a strong generated password, and a separate stable Grafana `secret_key`. Supply values through Secret references or mounted files supported by the selected image. Store recovery copies in the operator's password manager; commit only required key names and creation instructions. Do not embed actual or base64-encoded credentials in manifests, command history, transcripts, screenshots, or backups stored in Git.

Disable anonymous access and self-sign-up. Use the admin account for maintenance and a Viewer account for routine viewing if useful. Bootstrap credentials initialize a new database; changing the Kubernetes Secret alone does not rotate an existing account's password. Rotate the account through Grafana, then update the protected recovery record. Preserve the encryption key with a database backup so encrypted settings remain recoverable. [Grafana configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/) and [database encryption](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-database-encryption/)

Proposed operator access after deployment:

```powershell
kubectl -n forge-observability port-forward --address 127.0.0.1 service/grafana 3000:3000
```

Open `http://127.0.0.1:3000` while the command remains running. Port-forward authorization comes from the operator's kubeconfig, followed by Grafana login. The ClusterIP remains reachable by allowed in-cluster clients; port-forward-only describes external operator access, not network isolation inside Kubernetes. No new NetworkPolicy is proposed until existing policy and CNI enforcement are inventoried. Keep authenticated HTTP within the existing lab access model; external publication would require a separate access design.

## Initial dashboard scope

Build **two dashboards with six panels each**. Use built-in stat, time-series, state-timeline, and table panels. Default to the last 30 minutes, a 30-second refresh, and fixed five-minute rate windows matching the repository baseline. Set the Prometheus minimum interval to 30 seconds and label rates as five-minute rates. Avoid repeated panels and large variable combinations; the first version needs no dashboard variables.

| Dashboard | Six panels |
|---|---|
| Restaurant Overview | Healthy and discovered targets against expected 3; application request rate by route; application 5xx percentage; application p95 latency by route; healthy version coverage; analyze-feature state by healthy Pod |
| Scrape and Replica Diagnostics | Per-Pod scrape-health timeline; scrape duration by Pod; scraped sample count by Pod; application request rate by Pod; synthetic traffic rate by path and status; unmatched application requests by status |

The companion dashboard specification supplies exact candidate queries and empty-data behavior. A healthy scrape does not prove the NodePort is reachable or every application function works. Keep the existing API smoke checks. Expected replicas `3` is a documented baseline, not a live Deployment-spec metric. Histogram latency covers application middleware timing, not client-observed end-to-end latency.

The next optional dashboard is **Prometheus Collector Health**, requiring a separately reviewed self-scrape job first. It could show collector readiness, process memory, active series, block count, and ingestion. Verify exact metrics before defining panels. Do not infer filesystem free space or backup freshness from TSDB block size. Node, disk, Kubernetes workload-state, logs, traces, and alerting dashboards wait for an explicit collection decision.

## Backup and recovery

Keep Git as the recovery source for dashboards and nonsecret settings. Take a cold backup of Grafana's complete persistent data directory weekly and before upgrades or changes that affect the database. Retain the four newest successful weekly copies plus the most recent pre-upgrade copy until the upgrade is accepted. Backups are manual initially, with a dated success record; do not imply a scheduler exists.

1. Record the Git commit, image tag and digest, Grafana version, timestamp, PVC/PV identity, and filesystem UUID. Confirm the recovery credential and encryption-key records are available.
2. Scale only Grafana to zero and wait until no server Pod is using its data. Leave Prometheus collecting.
3. Archive the complete data directory through a narrowly scoped helper, preserving ownership and permissions. Copy it off-node to the NUC under `C:\Users\Michael Stipes\SignalForge-Backups\grafana`.
4. Compute SHA-256 and verify the copied archive. Protect backup access and encrypt its storage because account and session data are sensitive. Keep the encryption-key recovery copy separately protected.
5. In failure-safe cleanup, restore Grafana to one replica even if archival or copying fails. Verify rollout, login, the data source, and both dashboards. Record failures and do not prune older successful backups on a failed run.

Grafana's backup guidance requires stopping the service for a consistent SQLite copy. [Grafana backup guidance](https://grafana.com/docs/grafana/latest/administration/back-up-grafana/)

Proposed objectives: RPO no greater than seven days for mutable Grafana state, provided the weekly procedure succeeds; RTO no greater than one hour with a functioning cluster and prepared replacement storage. Full head-node or NVMe reconstruction is outside that RTO assumption. Neither objective is a measured result today.

Before implementation acceptance, verify the checksum, extract into an isolated path, and start the same pinned Grafana version against the restored copy using a separate temporary workload and localhost port-forward. Never mount the active Grafana PVC in the restore workload. Use the matching protected encryption key, verify login, stable dashboard UIDs and Prometheus queries, then record elapsed time from recovery start to usable dashboards. Remove only the verified isolated resources. An extraction or SQLite integrity check alone does not prove service recovery.

## Implementation sequence and rollback

After design agreement, prepare a focused repository branch and draft review using the existing contribution workflow. First add host-preparation instructions, manifests, dashboard JSON, validation, access helpers, and backup/restore procedures. Review the resource diff before touching the cluster.

Complete the storage and image preflights, create the new filesystem and retained PV/PVC, and use a temporary consumer to prove binding and writes before starting Grafana. With `WaitForFirstConsumer`, an unconsumed claim can remain Pending; a preflight Pod makes the storage gate testable. Remove the preflight Pod before the Grafana server starts.

Deploy and verify Grafana, then collect the acceptance evidence below. Grafana does not require any Prometheus configuration change for the two initial dashboards.

For the first installation, rollback means scale Grafana to zero and remove its Service if desired, retaining its PVC/PV, files, and secrets for investigation. Do not delete `forge-observability`, alter the Prometheus workload, or remove the shared StorageClass. For later upgrades, protect the current database and restore the previous matching image, configuration, and pre-upgrade database copy; a Deployment image rollback alone may not reverse schema migrations.

## Acceptance criteria

Milestone 027 planning acceptance:

- [x] Reviewed the repository at the supplied commit and mapped dashboard requirements to existing metrics.
- [x] Defined workload, resource budgets, storage isolation, provisioning, credentials, access, recovery, and rollback.
- [x] Defined two initial dashboards and explicitly deferred unavailable telemetry.
- [x] Preserved Milestone 026 limitations and made no deployment or disk changes.
- [x] Operator agreed to this design on 2026-09-10, including separate small persistent storage and manual backup responsibility.

Subsequent implementation acceptance requires recorded evidence:

- [ ] Pinned image supports ARM64; non-root identity and selected configuration are verified. Repository manifest and dashboard checks pass, and the reviewed apply diff contains only intended resources.
- [ ] Physical inventory confirms safe new allocation; Prometheus partition boundaries and UUID remain unchanged. New UUID mount, missing-mount protection, permissions, PV reservation, and PVC binding pass.
- [ ] Exactly one Ready Grafana Pod runs on `forge-head`. Resource requests fit allocatable capacity. No broad RBAC, automatic API token, extra platform, or public Service is introduced.
- [ ] Loopback port-forward works; authentication is required; anonymous access and sign-up are disabled; credentials are absent from tracked files and evidence.
- [ ] Provisioned data source passes a query. Exactly two dashboards and twelve panels load without errors. Dashboard updates preserve UIDs and do not duplicate dashboards.
- [ ] Three healthy targets and expected version coverage match Prometheus. A bounded request run over at least two scrape intervals produces traffic and latency data; a 404 exercise appears under `path="unmatched"`. Do not manufacture live 5xx failures solely for testing; validate error-rate logic against fixtures if needed.
- [ ] Idle traffic, absent series, down targets, and a failed data-source request are distinguishable. Missing data is not shown as healthy zero traffic or zero latency.
- [ ] Observe both dashboards with one operator for 30 minutes, recording periodic `kubectl top` samples for Grafana and Prometheus. No OOM, unexpected restarts, persistent query failures, or repeated dashboard loads above five seconds; investigate sustained Grafana memory above 80 percent of its limit. These are proposed lab criteria, not upstream guarantees.
- [ ] Replace the Grafana Pod and verify accounts, preferences, dashboards, and data-source configuration survive.
- [ ] Off-node backup verifies and isolated service restore passes login and queries. Record measured RPO/RTO and distinguish objectives that remain unproven.
- [ ] Practice the initial-install rollback and return while preserving Grafana storage. Restaurant API remains at three replicas, Prometheus retains its storage and three healthy targets, and `kubectl top` still works with secure kubelet validation.
- [ ] Update project status, architecture, operator guidance, and implementation milestone with actual outcomes and remaining limitations.

## Repository evidence

- [Project status at the reviewed commit](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/docs/project-status.md)
- [Milestone 026 evidence and limitations](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/docs/milestones/milestone-026-persistent-prometheus-storage.md)
- [Prometheus scrape configuration](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/k8s/prometheus/prometheus-config.yaml)
- [Application instrumentation](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/apps/restaurant-api/main.py)
- [PromQL baseline](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/docs/observability/prometheus-queries.md)

Suggested repository destination after agreement: `docs/milestones/milestone-027-lightweight-grafana-planning.md`. Keep this document's proposed values distinct from current-state architecture until implementation is verified.
