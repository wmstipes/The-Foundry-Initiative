# Project Status

**Last updated:** 2026-09-12

**Current phase:** Operational visibility and durable monitoring

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API, lightweight Prometheus, Kubernetes Metrics Server, Grafana, and the browser-local Forge YAML Workbench.

The project has moved from basic workload deployment into repeatable engineering operations: automated tests, GitHub Actions, ARM64 image publishing, version-controlled Kubernetes manifests, validation, helper commands, application metrics, and current node and Pod resource visibility.

## Current application

- Application: SignalForge Restaurant API
- Namespace: `forge-restaurant`
- Deployment: `restaurant-api`
- Replicas: 3
- Release: `0.7.0`
- Image: `wmstipes/signalforge-restaurant-api:0.7.0`
- External lab access: NodePort `30080`
- Metrics endpoint: `/metrics`

## Current Forge YAML Workbench state

- Application: Forge YAML Workbench
- Namespace: `forge-tools`
- Deployment: `forge-yaml-workbench`
- Replicas: 1 available and Ready
- Release: `0.1.2`
- Image: `wmstipes/signalforge-yaml-workbench:0.1.2@sha256:07f34be33c55bca5b7bf5321e5d149e4831ce520c9efbdd98233468a1a50e3c7`
- Runtime ImageID: verified against the pinned OCI index digest
- External lab access: NodePort `30081`
- Data path: browser-local parsing and analysis; no server-side YAML persistence
- Kubernetes identity: no mounted ServiceAccount token and no RBAC access
- Security: restricted namespace, non-root execution, RuntimeDefault seccomp, read-only root filesystem, and all capabilities dropped
- Acceptance: health and page responses passed; multi-document and visible-format browser regressions passed

## Completed milestones

- 001-009: Cluster foundation and initial Restaurant API workload
- 010: Restaurant API CI
- 011: Automated Docker build
- 012: Versioned release `0.5.0`
- 013: Kubernetes manifests under version control
- 014: Laptop `kubectl` access
- 015: Deployment helper and smoke test
- 016: SignalForge operator command helper
- 017: Operator runbook
- 018: Kubernetes manifest validation in CI
- 019: Developer command layer
- 020: Basic application observability with `/metrics`
- 021: Metrics collection planning
- 022: Lightweight Prometheus metrics collection
- 023: Application metrics refinement
- 024: Kubernetes Metrics Server evaluation and secure kubelet PKI
- 025: Persistent Prometheus storage planning
- 026: Persistent Prometheus storage implementation and recovery validation
- 027: Lightweight Grafana design and dashboard requirements accepted
- 028: Lightweight Grafana implementation, persistence and recovery validation
- 029: Limited alerting design accepted and merged
- 030: Limited alerting rules validated, activated and verified without notification delivery
- 032: Forge YAML Workbench `0.1.1` built, published, hardened, deployed and browser-validated
- 033: Workbench usability improved; `0.1.2` published, digest-pinned, deployed and live browser-validated

## Current observability state

- Prometheus namespace: `forge-observability`
- One Prometheus replica
- Image: `prom/prometheus:v3.13.2`
- Pod discovery restricted to `forge-restaurant`
- RBAC restricted to get, list, and watch Pods
- Scrape interval: 30 seconds
- Retention: 30 days or 24 GB
- Storage: 30 GiB retained local PV on the head NVMe
- Access: ClusterIP plus `kubectl port-forward`
- Healthy Restaurant API targets: 3
- Prometheus Pod: stable with zero restarts after rollout
- Automatic target rediscovery: confirmed through application Pod replacement
- Request-duration histogram: available across all three application Pods
- Traffic classification: `application` and `synthetic`
- Cardinality protection: unmatched URLs use `path="unmatched"`
- Baseline queries: `docs/observability/prometheus-queries.md`
- Alert evaluator: two Restaurant API scrape-coverage rules loaded by Prometheus
- Alert state at acceptance: both rules `health=ok` and `state=inactive`
- Trial delays: five-minute warning and two-minute critical, still provisional operational thresholds
- Alert delivery: none; no Alertmanager or receiver is configured
- Alert rollback: validated baseline ConfigMap retained off-cluster with SHA-256 recorded in Milestone 030

## Current Grafana state

- Namespace: `forge-observability`
- Deployment: `grafana`
- Replicas: 1
- Grafana OSS version: `13.2.1`
- Image: `grafana/grafana:13.2.1@sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283`
- Access: ClusterIP plus authenticated `kubectl port-forward`; anonymous dashboard access is rejected
- Storage: 3 GiB retained local PV `grafana-local-nvme` on the `forge-head` NVMe
- Filesystem UUID: `a506c674-127a-46da-9c7d-d158b6d1bb75`
- Mount: `/mnt/signalforge-grafana`
- Dashboards: SignalForge Restaurant Overview and SignalForge Scrape Diagnostics
- Dashboard panels: 12 total, with provisioned Prometheus data source and stable dashboard/data-source UIDs
- Healthy Restaurant API targets represented in dashboards: 3
- Pod replacement persistence: confirmed for database-backed personal settings
- Extended observation: zero Grafana restarts; sampled use approximately 5m CPU and 192-202 MiB memory
- Dashboard responsiveness: no load above five seconds observed during acceptance checks
- Cold backup: verified off-node with independent SHA-256 validation
- Isolated restore: passed authentication, provisioning, dashboard queries, browser rendering and persisted-setting recovery
- Restore readiness: 41 seconds
- Measured recovery time through usable validated dashboards: 262 seconds / 4.37 minutes
- Recovery objective: demonstrated inside the one-hour Grafana RTO target
- Rollback/return: passed while retaining Grafana storage and credentials and preserving Prometheus collection
- Protected recovery material: Grafana admin username, password and encryption `secret-key` stored independently in the password manager
- Backup cadence: weekly and before upgrades when appropriate; four successful weekly archives retained manually

## Current Kubernetes resource-metrics state

- Metrics Server namespace: `kube-system`
- Deployment: `metrics-server`
- Image: `registry.k8s.io/metrics-server/metrics-server:v0.9.0`
- Replicas: 1
- Metrics API: `metrics.k8s.io/v1beta1`
- Collection interval: 15 seconds
- Node address preference: `InternalIP,ExternalIP,Hostname`
- Kubelet TLS: verified with the Kubernetes service-account CA
- Insecure kubelet TLS flag: not used
- Kubelet serving certificates: Kubernetes-CA-signed with hostname and InternalIP SANs
- Live node coverage: 4 of 4 nodes
- Observed Metrics Server footprint: 4m CPU and 21 MiB memory
- `kubectl top nodes` and `kubectl top pods`: available

## Persistent-storage implementation

Milestone 025 selected the following Prometheus storage target:

- Dedicated 32 GiB ext4 partition on the verified `forge-head` Samsung SSD 950 PRO 512GB NVMe
- Static 30 GiB Kubernetes `local` PV and PVC
- Non-default `signalforge-local-nvme` StorageClass with `WaitForFirstConsumer`
- `ReadWriteOnce` access, `Retain` reclaim policy, and exact `forge-head` PV node affinity
- One Prometheus replica using the `Recreate` strategy
- Retention of 30 days or 24 GB, whichever is reached first
- Weekly cold backups copied off `forge-head`, with the four newest retained
- Recovery objectives of RPO at or below 7 days and RTO at or below 1 hour
- Existing ClusterIP and `kubectl port-forward` access model preserved

Milestone 026 host preparation is complete:

- Verified `/dev/nvme0n1` as Samsung SSD 950 PRO 512GB, serial `S2GMNCAGB06236R`
- Backed up the prior partition table before the explicitly approved disk erase
- Completed a destructive four-pattern write/read test of the new 32 GiB partition with zero bad blocks
- Confirmed the NVMe media-error count remained 215 before and after that test
- Created ext4 filesystem UUID `4f2feee5-72a7-4f32-a351-b4253c4a0854`
- Mounted the filesystem by UUID at `/mnt/signalforge-prometheus`
- Created `data` as `65534:65534` with mode `0750` and verified writes as that identity
- Proved the data path disappears when the NVMe is unmounted, preventing silent SD-card fallback writes

The NVMe cutover is live. Pod-replacement persistence and six-block off-node backup/restore validation passed. See Milestone 026 for the checksum and evidence.

## Immediate next step

Milestone 028 is complete. Lightweight Grafana is deployed with retained storage, provisioned SignalForge dashboards, tested persistence, encrypted off-node backup, isolated restore, credential recovery and rollback/return.

The Milestone 029 [limited-alerting design](observability/limited-alerting-specification.md) was accepted by Mike and merged through PR #4 at `1837868` on 2026-09-10. It covers reduced scrape coverage and no-healthy-target conditions using the manual three-replica baseline. Five-minute and two-minute delays remain provisional, not measured operational thresholds. Performance alerts, notification channels, Alertmanager, and broader monitoring coverage remain deferred.

[Milestone 030](milestones/milestone-030-limited-alerting-implementation.md) is complete. Its offline package merged through PR #5 at `604e38e` after real promtool 3.13.2 passed both rules and all 19 scenarios. The guarded activation candidate merged through PR #6 at `f54b961`. After explicit approval on 2026-09-11, only the Prometheus ConfigMap changed and only Prometheus restarted. Immediate and independent checks confirmed three healthy targets, an exact live/repository configuration match, and both accepted rules loaded, healthy and inactive. A checksum-recorded baseline recovery file is retained. No Alertmanager, receiver or notification delivery exists.

`Milestone 032` is complete and merged through PR #8 at `3b6bac5`.

`Milestone 033` is complete and merged through PR #9 at `7aadedd`. Forge YAML Workbench `0.1.2` runs as one Ready replica with zero restarts from the pinned OCI index digest. NodePort routing, `/healthz`, the application page, security headers, sample loading, format feedback, editing state, the format shortcut, and YAML download all passed live verification.

Milestone 034 is in progress as a source-only Workbench increment. It adds deeper deterministic Kubernetes checks with precise YAML paths, explanations, and suggested corrections while preserving browser-local analysis. Release publication and live deployment remain separate future checkpoints. Continue observing naturally occurring alert behavior without injecting a failure merely to produce firing evidence.

## Known temporary limitation

Prometheus and Grafana remain dependent on `forge-head` and its local NVMe during head-node or device failure. Weekly off-node backups remain manual. Grafana service recovery from an accepted backup was measured at 4.37 minutes on a functioning cluster, but full head-node or NVMe reconstruction remains outside that result. Prometheus full service-restoration timing remains a separate limitation.

Kubelet serving-certificate rotation can create new pending CSRs. Core Kubernetes does not automatically approve these serving requests, so an operator must validate the requester, signer, usages, subject, and SAN ownership before approval.

Forge YAML Workbench performs YAML parsing and bounded operational review, not complete Kubernetes OpenAPI validation or admission testing. NodePort `30081` uses plain HTTP and is intended only for the private lab. Complete browser-local schema validation remains deferred to Milestone 035.
