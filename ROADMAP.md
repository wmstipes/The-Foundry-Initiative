# The Foundry Initiative Roadmap

**Last updated:** 2026-09-11

The roadmap favors small, demonstrable outcomes over large unfinished plans. It describes direction and sequencing; detailed implementation evidence belongs in `docs/milestones`, and the live system state belongs in `docs/project-status.md`.

## Current position

The active workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. Milestones 001-030 are complete, and Restaurant API `0.7.0` is running as three replicas with automated delivery, version-controlled Kubernetes manifests, operator tooling, lightweight Prometheus metrics collection, Kubernetes resource metrics, Grafana visualization, and a limited Prometheus rule-evaluation layer. NVMe-backed Prometheus and Grafana both use retained local storage with tested persistence and recovery procedures.

Milestone 029's documentation-only limited-alerting design was accepted and merged on 2026-09-10 at `1837868`. Milestone 030's offline rules passed all 19 pinned-promtool scenarios and merged through PR #5 at `604e38e`; its guarded activation candidate merged through PR #6 at `f54b961`. On 2026-09-11, explicit approval preceded successful ConfigMap-only activation and independent verification of two healthy inactive rules with three healthy targets. The delays remain provisional, and no notification delivery is configured.

## Phase 1 — Cluster and application foundation

**Status:** Complete

Delivered outcomes:

- Raspberry Pi Kubernetes cluster brought online.
- Initial workloads deployed and validated.
- FastAPI Restaurant API containerized for `linux/arm64`.
- Deployment, Services, ConfigMap, probes, and resource controls introduced.
- Rolling update, rollback, and roll-forward procedures practiced.
- External lab access and API smoke testing established.

Related milestones: 001-009.

## Phase 2 — Release engineering and repeatable operations

**Status:** Complete

Delivered outcomes:

- Restaurant API automated tests and GitHub Actions CI.
- Automated ARM64 image publishing to Docker Hub.
- Versioned application releases.
- Kubernetes manifests and validation stored in Git.
- Laptop-based `kubectl` access.
- Deployment, smoke-test, status, image, Pod, and log helpers.
- Operator runbook and developer preflight workflow.

Related milestones: 010-019.

## Phase 3 — Initial observability layer

**Status:** Complete

Delivered outcomes:

- Prometheus-format application metrics at `/metrics`.
- Lightweight metrics-collection architecture selected for the Pi cluster.
- Single in-cluster Prometheus collector with least-privilege Pod discovery.
- Three independent Restaurant API scrape targets.
- Request-duration histogram suitable for cross-replica aggregation.
- Application and synthetic traffic classification.
- Bounded route labels that protect metric cardinality.
- Baseline PromQL queries for health, traffic, errors, and latency.

Related milestones: 020-023.

## Phase 4 — Operational visibility and durable monitoring

**Status:** In progress

### Milestone 024 — Kubernetes Metrics Server evaluation

**Status:** Complete

Delivered outcomes:

- Repaired kubelet serving PKI without disabling TLS verification.
- Enabled durable kubelet serving-certificate bootstrap configuration.
- Deployed pinned Metrics Server v0.9.0 on ARM64.
- Enabled and validated `kubectl top nodes` and `kubectl top pods` across all four nodes.
- Measured an observed Metrics Server footprint of 4m CPU and 21 MiB memory.
- Retained Metrics Server based on its low footprint and immediate operational value.
- Preserved Prometheus as the separate historical application-metrics system.

### Milestone 025 — Persistent Prometheus storage planning

**Status:** Complete

Delivered outcomes:

- Selected a static Kubernetes `local` PV backed by a dedicated ext4 partition on the `forge-head` NVMe.
- Defined a 32 GiB partition, 30 GiB PV/PVC, and 30-day or 24 GB Prometheus retention limits.
- Made `forge-head` placement and the lack of automatic node failover explicit through PV node affinity.
- Chose a non-default `WaitForFirstConsumer` StorageClass without a dynamic provisioner.
- Defined weekly off-node cold backups, four-backup retention, and recovery objectives.
- Documented missing-mount safeguards, recovery behavior, migration, and rollback.
- Preserved the current live `emptyDir` deployment until implementation validation.

### Milestone 026 — Persistent Prometheus storage implementation

**Status:** Complete. NVMe preparation, deployment, persistence, backup/restore analysis, UI access, and storage rollback/return validation passed.

### Milestone 027 — Lightweight Grafana planning

**Status:** Complete

Delivered outcomes:

- Defined a lightweight Grafana architecture appropriate for the Raspberry Pi cluster.
- Selected a pinned ARM64-compatible Grafana OSS image and conservative resource limits.
- Defined retained local storage, authenticated localhost access, least-privilege runtime controls, provisioning, backup, restore, and rollback requirements.
- Designed two purpose-built SignalForge dashboards with twelve total panels.
- Defined persistence, resource-observation, recovery, and rollback acceptance criteria before implementation.

### Milestone 028 — Lightweight Grafana implementation

**Status:** Complete

Delivered outcomes:

- Deployed Grafana OSS 13.2.1 with a pinned image digest.
- Provisioned the SignalForge Restaurant Overview and SignalForge Scrape Diagnostics dashboards.
- Added a retained 3 GiB local PV/PVC backed by the `forge-head` NVMe.
- Verified authenticated localhost access and rejection of anonymous dashboard access.
- Confirmed dashboard queries, idle/missing-data behavior, representative traffic, and three healthy Restaurant API targets.
- Verified database-backed settings survive Pod replacement and complete scale-to-zero rollback/return.
- Observed stable Grafana resource use with zero restarts during acceptance.
- Created and checksum-verified an encrypted off-node cold backup.
- Restored the accepted backup into an isolated Pod without mounting the production PVC.
- Measured 41 seconds to restore-Pod readiness and 262 seconds / 4.37 minutes through usable validated dashboards.
- Verified independent protected recovery of Grafana administrative credentials and encryption key.
- Confirmed Prometheus continued collecting all three application targets while Grafana was intentionally stopped.

### Milestone 029 — Limited alerting planning

**Status:** Complete. Accepted and merged on 2026-09-10 through PR #4 at `1837868`.

Bounded outcomes:

- Propose two mutually exclusive service-level scrape-coverage conditions using the existing Restaurant API metrics.
- Document provisional delays, missing-data behavior, the manual three-replica baseline, first-response guidance, and monitoring-system blind spots.
- Define future offline tests and evidence requirements before activation.
- Defer performance thresholds, notification channels, Alertmanager, and broader telemetry.
- Reconcile historical error-ratio documentation and Grafana specification status without changing runtime configuration.

See [Milestone 029](docs/milestones/milestone-029-limited-alerting-planning.md) and the [limited-alerting specification](docs/observability/limited-alerting-specification.md). Planning acceptance and version control are complete; this does not establish live alerting coverage.

### Milestone 030 — Limited alerting implementation

**Status:** Complete. Offline validation, guarded activation, recovery capture and live verification passed.

- Implement two candidate scrape-coverage rules and validate them before wiring.
- Validate static boundaries and generate 19 synthetic scenarios for pinned-promtool evaluation.
- Offline CI passed both rule validation and all 19 scenarios on 2026-09-10; PR #5 merged at `604e38e`.
- Activated only the ConfigMap wiring after a read-only live plan and explicit approval; retained a checksum-recorded recovery snapshot and verified an exact live/repository match.
- Confirmed three healthy targets and two loaded rules with healthy inactive state; no receiver or notification path was added.

See [Milestone 030](docs/milestones/milestone-030-limited-alerting-implementation.md) and the [activation review](docs/observability/limited-alerting-activation-review.md). No receiver or notification delivery is included.

### Later outcomes in this phase

- Observe naturally occurring alert behavior and revisit provisional delays before designing notification delivery.
- Continue exercising backup cadence and recovery procedures so RPO assumptions remain demonstrated over time.
- Reevaluate whether the lightweight collector remains sufficient before considering `kube-prometheus-stack`.

## Phase 5 — Platform access and broader telemetry

**Status:** Planned

Potential outcomes:

- Introduce Ingress as a cleaner application-access pattern.
- Add TLS and document certificate management for the private lab.
- Evaluate centralized logging, with Loki as a candidate rather than a predetermined choice.
- Evaluate OpenTelemetry for traces and correlated application signals.
- Improve cluster and application security controls as externally reachable components expand.

Each telemetry layer should answer a specific operational question before it is installed.

## Phase 6 — ForgeOps AI-assisted operations

**Status:** Planned

Evolve the rules-based `/analyze` endpoint into a grounded Kubernetes incident copilot.

Potential outcomes:

- Collect a bounded, read-only snapshot of relevant Kubernetes state.
- Normalize incidents, symptoms, events, logs, and metrics into a structured schema.
- Combine deterministic checks with retrieval and language-model reasoning where each adds value.
- Cite the evidence used for every diagnosis and recommendation.
- Evaluate ForgeOps against repeatable failure scenarios.
- Preserve human approval for operational changes; autonomous cluster mutation is out of scope until explicit safety criteria exist.

## Phase 7 — Portfolio and hybrid-cloud expansion

**Status:** Planned

Potential outcomes:

- Turn SignalForge into a concise architecture and operations case study.
- Capture diagrams, design tradeoffs, failure investigations, and measurable outcomes.
- Identify components that can be reused in future Kubernetes projects.
- Extend a carefully selected SignalForge capability into AWS to demonstrate hybrid-cloud architecture.
- Introduce infrastructure as code when the target architecture is stable enough to benefit from it.
- Compare cost, operations, security, and reliability between the local lab and cloud extension.

Portfolio documentation and reflection should continue throughout the roadmap rather than wait until the final phase.

## Sequencing guardrails

- Complete one bounded milestone before opening the next.
- Prefer measurement and evaluation before installing a larger platform component.
- Keep changes reversible while the architecture is still evolving.
- Avoid adding tools solely because they are common in production stacks.
- Update architecture, status, runbook, milestone, and learning documentation when their facts materially change.
- Preserve the lab as a place for learning and recovery, not a source of unsustainable operational burden.

## Definition of done

A milestone is complete when:

- its intended result is usable
- implementation and configuration are version controlled
- appropriate automated or manual tests pass
- the live outcome is verified when deployment is involved
- operating steps and known limitations are documented
- the milestone record contains enough evidence for someone returning later
- the next step is identified without silently expanding the completed milestone's scope
