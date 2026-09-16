# Project Status

**Last updated:** 2026-09-16

**Current phase:** Operational visibility and ForgeOps snapshot implementation

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API, lightweight Prometheus, Kubernetes Metrics Server, Grafana, and the browser-local Forge YAML Workbench.

The project has moved from basic workload deployment into repeatable engineering operations: automated tests, GitHub Actions, ARM64 image publishing, version-controlled Kubernetes manifests, validation, helper commands, application metrics, and current node and Pod resource visibility. Milestone 044 defined and live-feasibility-tested the bounded read-only evidence contract. Milestone 045 now implements that contract locally with deterministic evaluation and offline tests; publication and live execution remain separately gated.

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
- Release: accepted `0.10.0` deployed
- Image: `wmstipes/signalforge-yaml-workbench:0.10.0@sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`
- Runtime ImageID: verified against the pinned OCI index digest
- External lab access: NodePort `30081`
- Data path: browser-local parsing and analysis; no server-side YAML persistence
- Modes: Kubernetes inspection by default and explicit General YAML inspection for mapping, sequence, and scalar roots
- Kubernetes identity: no mounted ServiceAccount token and no RBAC access
- Security: restricted namespace, non-root execution, RuntimeDefault seccomp, read-only root filesystem, and all capabilities dropped
- Acceptance: immutable `0.10.0` is deployed; generation 14, configured and runtime digests, one Ready Pod on `forge-node-03` with zero restarts, one ready EndpointSlice endpoint, NodePort health and page responses, security headers, and the complete live file-drop workflow passed
- Validation filters: counted All, Errors, Warnings, Notes, and Valid views preserve the complete analysis for the tab badge, overall status, OWASP coverage, and Markdown reports
- Tree search: Milestone 041 provides literal key, scalar-value, and canonical-path matching with deterministic counted navigation, automatic ancestor expansion, highlighting, accessible keyboard behavior, and explicit state boundaries
- File drop: Milestone 042 provides visible one-file YAML drag-and-drop, shared unsaved-change protection, explicit state preservation and reset boundaries, keyboard-equivalent opening, and browser-navigation prevention

## Current documentation front-door state

- Milestone: 043, complete and cleaned up
- Purpose: curated navigation for recruiters, technical reviewers, operators, and learners
- Authority: repository documentation remains authoritative
- Repository source: `docs/wiki/Home.md` and `docs/wiki/_Sidebar.md`
- Validation: offline structure, link-target, stable-content, workflow-trigger, exact-copy, and browser checks passed
- Live Wiki: published and accepted at `0a945b4cac2ba1c781a55f9aa1a8c389426892e3`
- Repository merge: PR #25 merged at `c42614db59f8b42a3d5e90d0a9e4272f47ed8080`; closeout PR #26 merged at `90c4b369516881943ed3c00d1070f7c70b5fc7ae`
- Restaurant API image workflow: documentation-only `main` pushes now skip publication, while Restaurant API source changes, version tags, and manual dispatch remain enabled
- Cleanup: all `codex/milestone-*` branches were removed locally and remotely; the intentionally preserved older remote branches are unchanged

## Current ForgeOps state

- Milestone: 044, design complete and merged through PR #27 at `c467468`
- Goal: define a separate local, read-only SignalForge health snapshot before implementation
- Target evidence: expected nodes, five named Deployments and their Pods, allowlisted EndpointSlices, Metrics APIService availability, and explicitly configured application endpoints
- Output contract: one normalized `forgeops.snapshot/v1alpha1` model with equivalent terminal and Markdown views
- Safety boundary: explicit kubeconfig and context, closed read-command allowlist, bounded output, redaction, no broad discovery, no sensitive objects, and no mutation
- Failure boundary: incomplete required evidence remains `UNKNOWN` and returns an incomplete-collection exit code rather than implying health
- Publication: branch `codex/milestone-044-forgeops-snapshot-design` contained design commit `c0cbfab` and live-evidence reconciliation commit `f42bc75`; the published and locally reviewed head trees matched exactly at `4a445e26`
- Live feasibility: exact context validation passed; four expected nodes were Ready; all five Deployments met desired, updated, ready, and available replica counts; seven selected Pods were Running and Ready with zero restarts; all expected EndpointSlice endpoints were ready; Metrics APIService was available; and all five bounded HTTP checks passed
- Runtime impact: read-only Kubernetes and HTTP feasibility queries only; there is no collector implementation, image, manifest, deployment, rollout, restart, Wiki mutation, or cluster mutation in this milestone
- Merge: PR #27 was marked ready after separate approval and merged into `main` at `c467468f8afa349af92f6af1601283449248c8a4` on 2026-09-16; the merge tree exactly matched the reviewed branch tree
- Checks: the operator confirmed all Actions shown in GitHub were green; the connected GitHub API exposed no workflow-run or commit-status records for either the head or merge commit
- Closeout and cleanup: closeout PR #28 merged at `aa178b0`; both Milestone 044 branches were removed locally and remotely
- Milestone 045: local `forgeops snapshot` implementation complete on `codex/milestone-045-forgeops-snapshot`
- Implementation: fixed SignalForge constants, deny-by-default kubectl and HTTP runners, selected-field normalization, deterministic evaluation, and terminal or Markdown rendering
- Test boundary: synthetic fixtures only; no test invokes kubectl or contacts a network
- Local package metadata: `0.2.0`, preserving `foundry-check` and adding `forgeops`
- Runtime impact: no live cluster or endpoint access, image, manifest, deployment, package registry, or Wiki change during local implementation
- Remaining Milestone 045 gates: publication, read-only live acceptance, PR readiness, merge, closeout, and cleanup

## Milestone 038 closeout

- Release: `0.6.0`
- Source acceptance: 58 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, AMD64/ARM64 non-publishing build, repository validation, whitespace validation, Windows build, and local browser interactions passed
- Behavior: valid formatting changes require explicit Apply or Cancel; invalid YAML remains unchanged and routes to Validation
- Release acceptance: the AMD64/ARM64 OCI index was independently digest-verified, deployed after an approved Deployment-only diff, and passed runtime, HTTP, security-header, and live browser validation

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
- 034: Workbench deterministic Kubernetes checks and actionable remediation released as `0.2.0`, deployed, accepted, and merged
- 035: General YAML inspection released as `0.3.0`, deployed, live browser-accepted, and merged
- 036: corrected `0.4.1` published, digest-pinned, deployed, live browser-accepted, and merged through PR #13 at `fc16ad1`
- 037: pinned OWASP Kubernetes Top 10:2025 review profile and corrected finding navigation released as `0.5.1`, deployed, browser-accepted, and squash-merged through PR #14 at `dd46a08`
- 038: browser-local formatting preview released as `0.6.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #16 at `4fed28c`
- 039: browser-local Markdown reports released as immutable `0.7.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #18 at `1e0c525`
- 040: Validation result filters released as immutable `0.8.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #20 at `6fa5092`
- 041: browser-local YAML Tree search released as immutable `0.9.0`, deployed, accepted, merged through PR #22 at `0f3d44e`, and cleaned up
- 042: safe browser-local YAML file drop released as immutable `0.10.0`, deployed, accepted, and merged through PR #23 at `020d5e7`
- 043: curated repository-owned GitHub Wiki front door published, browser-accepted, merged, and cleaned up; documentation-only Restaurant API image publication is suppressed

## Latest release milestone

- 042: safe browser-local one-file YAML drop with visible and accessible target states, shared unsaved-change protection, deterministic state boundaries, and keyboard-equivalent opening
- Trust boundary: browser-provided basename and contents remain in memory; no upload, backend, persistence, telemetry, cluster credentials, Kubernetes API access, or automatic remediation
- Verification: 92 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, repository validation, whitespace checks, Windows validation, CI, AMD64/ARM64 builds, and source and live browser reviews passed
- Publication and deployment: immutable AMD64/ARM64 `0.10.0` is live at OCI index `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`
- Runtime acceptance: generation 14, one Ready Pod on `forge-node-03`, zero restarts, exact configured/runtime digest match, one ready endpoint at `10.244.54.203:8080`, fresh HTTP 200 responses, expected security headers, and the complete file-drop workflow passed
- Completion record: release and acceptance evidence merged through PR #23 at `020d5e7`; post-merge branch cleanup is complete

## Previous completed milestone

- 040: counted Validation result filters with level isolation, empty-section handling, edit-time recomputation, reset boundaries, and complete-report isolation
- Trust boundary: ephemeral browser-local presentation state; no backend, persistence, telemetry, cluster credentials, Kubernetes API access, or automatic remediation
- Verification: 74 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, repository validation, whitespace checks, Windows validation, CI, AMD64/ARM64 build, and source and live browser reviews passed
- Publication and deployment: immutable AMD64/ARM64 `0.8.0` was released at OCI index `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`
- Completion: PR #20 merged at `6fa5092`; Workbench CI run 142, Kubernetes Manifest Validation run 124, and Restaurant API Docker Build run 57 passed on `main`

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

Review the local Milestone 045 implementation and offline evidence. Branch publication and draft PR creation require separate approval; live read-only acceptance remains a later independent gate.

## Supporting completed work

Lightweight Grafana remains deployed with retained storage, provisioned SignalForge dashboards, tested persistence, encrypted off-node backup, isolated restore, credential recovery and rollback/return.

The Milestone 029 [limited-alerting design](observability/limited-alerting-specification.md) was accepted by Mike and merged through PR #4 at `1837868` on 2026-09-10. It covers reduced scrape coverage and no-healthy-target conditions using the manual three-replica baseline. Five-minute and two-minute delays remain provisional, not measured operational thresholds. Performance alerts, notification channels, Alertmanager, and broader monitoring coverage remain deferred.

[Milestone 030](milestones/milestone-030-limited-alerting-implementation.md) is complete. Its offline package merged through PR #5 at `604e38e` after real promtool 3.13.2 passed both rules and all 19 scenarios. The guarded activation candidate merged through PR #6 at `f54b961`. After explicit approval on 2026-09-11, only the Prometheus ConfigMap changed and only Prometheus restarted. Immediate and independent checks confirmed three healthy targets, an exact live/repository configuration match, and both accepted rules loaded, healthy and inactive. A checksum-recorded baseline recovery file is retained. No Alertmanager, receiver or notification delivery exists.

`Milestone 032` is complete and merged through PR #8 at `3b6bac5`.

`Milestone 033` is complete and merged through PR #9 at `7aadedd`. Forge YAML Workbench `0.1.2` runs as one Ready replica with zero restarts from the pinned OCI index digest. NodePort routing, `/healthz`, the application page, security headers, sample loading, format feedback, editing state, the format shortcut, and YAML download all passed live verification.

Milestone 034 published, immutably pinned, deployed, and live browser-validated the approved `0.2.0` AMD64/ARM64 image, then merged through PR #10 at `9848618`. The running Pod is Ready with zero restarts and its runtime ImageID matches the reviewed OCI index digest.

Milestone 035 published and deployed its separately approved `0.3.0` AMD64/ARM64 image at OCI index digest `sha256:3abd4292f6cbd506dbc976924d2b61cf8093a7653e02654efaedc207e3f3086f`. It adds an explicit General YAML mode alongside the default Kubernetes mode. Both modes share browser-local parsing, formatting, parser diagnostics, file handling, and tree navigation. General YAML accepts mappings, sequences, and scalars while omitting Kubernetes-only findings. The Deployment-only rollout completed with one Ready replica, zero restarts, a matching runtime ImageID, ready routing, HTTP 200 responses, both mode markers, and the expected security headers. Live browser interaction acceptance passed, and PR #11 merged at `b45ee0b`.

Continue observing naturally occurring alert behavior without injecting a failure merely to produce firing evidence.

## Known temporary limitation

Prometheus and Grafana remain dependent on `forge-head` and its local NVMe during head-node or device failure. Weekly off-node backups remain manual. Grafana service recovery from an accepted backup was measured at 4.37 minutes on a functioning cluster, but full head-node or NVMe reconstruction remains outside that result. Prometheus full service-restoration timing remains a separate limitation.

Kubelet serving-certificate rotation can create new pending CSRs. Core Kubernetes does not automatically approve these serving requests, so an operator must validate the requester, signer, usages, subject, and SAN ownership before approval.

Forge YAML Workbench `0.10.0` is deployed from the published AMD64/ARM64 OCI index at `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`. Its runtime, safe YAML file drop, Tree search, formatting preview, Markdown report workflow, Validation filters, OWASP profile, schema boundaries, General YAML isolation, strict headers, and corrected finding-link scrolling passed live acceptance. NodePort `30081` remains private-lab HTTP exposure.
