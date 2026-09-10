# The Foundry Initiative Roadmap

**Last updated:** 2026-09-10

The roadmap favors small, demonstrable outcomes over large unfinished plans. It describes direction and sequencing; detailed implementation evidence belongs in `docs/milestones`, and the live system state belongs in `docs/project-status.md`.

## Current position

The active workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. Milestones 001-025 are complete, and Restaurant API `0.7.0` is running as three replicas with automated delivery, version-controlled Kubernetes manifests, operator tooling, lightweight Prometheus metrics collection, and Kubernetes resource metrics. NVMe-backed Prometheus is deployed, with persistence and isolated backup/restore validation passed; Milestone 026 still has port-forward and rollback acceptance checks open.

The project is moving from its initial application-observability layer into broader operational visibility.

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

**Status:** In progress. NVMe preparation, deployment, Pod-replacement persistence, three-target health, and isolated off-node backup/restore validation passed. Finish port-forward verification and rollback testing before closing the milestone.

### Later outcomes in this phase

- Establish practical retention, backup, and recovery expectations.
- Add a small Grafana deployment with purpose-built SignalForge dashboards.
- Add a limited alerting layer only after normal behavior and useful thresholds are understood.
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
