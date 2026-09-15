# The Foundry Initiative Roadmap

**Last updated:** 2026-09-15

The roadmap favors small, demonstrable outcomes over large unfinished plans. It describes direction and sequencing; detailed implementation evidence belongs in `docs/milestones`, and the live system state belongs in `docs/project-status.md`.

## Current position

The active workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. Milestones 001-030 and 032-040 are complete. Restaurant API `0.7.0` runs as three replicas alongside lightweight Prometheus, Kubernetes Metrics Server, Grafana, bounded rule evaluation, and Forge YAML Workbench. NVMe-backed Prometheus and Grafana use retained local storage with tested persistence and recovery procedures; the Workbench is intentionally stateless and performs analysis in the browser. Milestone 041's browser-local YAML tree search runs as immutable Workbench `0.9.0`; its accepted release and closeout evidence are carried together by PR #22.

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

### Milestone 032 — Forge YAML Workbench

**Status:** Complete. Source, CI, multi-architecture release, hardened deployment and browser acceptance passed.

Delivered outcomes:

- Built a browser-local Kubernetes YAML inspector with multi-document parsing, formatting, summaries, bounded operational findings, and an expandable object tree.
- Added locked dependencies, six analyzer tests, build and audit checks, and guarded AMD64/ARM64 image publication.
- Published corrected release `0.1.1` and pinned OCI index digest `sha256:50e3d115641941bc8f7eaa303463c08ccbafe5842cc07304d4b71dbd4aef8669`.
- Deployed one restricted, non-root, read-only replica in `forge-tools` through NodePort `30081`, without Kubernetes credentials or server-side YAML persistence.
- Found a multi-document formatting defect during browser acceptance, added a round-trip regression test, published the patch, and verified the corrected live behavior.

See [Milestone 032](docs/milestones/milestone-032-forge-yaml-workbench.md) and the [Workbench deployment guide](k8s/forge-yaml-workbench/README.md).

### Milestone 033 — Forge YAML Workbench usability

**Status:** Complete. Merged through PR #9 at `7aadedd` on 2026-09-12 after implementation, publication, approved deployment, and live browser acceptance passed.

Delivered outcomes:

- Add explicit action feedback, precise parser locations, and click-to-focus diagnostics.
- Preserve filenames, add keyboard shortcuts, and protect unsaved edits from accidental clearing.
- Add DOM interaction tests without changing the Workbench's local-only trust boundary.
- Publish and deploy immutable `0.1.2`, then verify its runtime digest, ready endpoint, health response, security headers, and live browser interactions.

See [Milestone 033](docs/milestones/milestone-033-workbench-usability.md).

### Workbench follow-ons

#### Milestone 034 — Deeper deterministic checks

**Status:** Complete and merged through PR #10 at `9848618`.

- Attach clickable YAML paths, explanations, recommended changes, copyable examples, operational cautions, and initial OWASP K01:2025 references to operational findings.
- Check workload selector consistency, duplicate resource identities, Service-to-workload selectors, named target ports, host namespaces, and container hardening settings.
- Keep all evaluation deterministic and browser-local; do not claim API-server schema or admission validation.

See [Milestone 034](docs/milestones/milestone-034-workbench-deterministic-checks.md).

#### Milestone 035 — General YAML inspection mode

**Status:** Complete. Published, digest-pinned, deployed, live browser-accepted, and merged through PR #11 at `b45ee0b`.

- Keep Kubernetes as the default and add an explicit General YAML mode.
- Share browser-local parsing, formatting, diagnostics, file handling, and tree navigation across modes.
- Accept mapping, sequence, and scalar roots in General YAML mode and summarize their shape.
- Suppress Kubernetes-only operational findings in General YAML mode.

See [Milestone 035](docs/milestones/milestone-035-general-yaml.md).

#### Milestone 036 — Browser-local Kubernetes schema validation

**Status:** Complete. Corrected `0.4.1` was published, digest-pinned, deployed, live browser-accepted, and merged through PR #13 at `fc16ad1`.

- Validate supported Kubernetes resources against schemas for one explicitly pinned Kubernetes version.
- Keep schema data and validation in the browser without adding cluster access or server-side YAML processing.
- Distinguish YAML syntax, deterministic operational findings, and schema-validation results in the report.
- Report unsupported resources and unavailable CRD schemas explicitly instead of treating them as valid or invalid.
- Preserve General YAML mode as syntax and structure inspection without Kubernetes schema findings.

See [Milestone 036](docs/milestones/milestone-036-browser-local-schema-validation.md).

#### Milestone 037 — Pinned OWASP Kubernetes Top 10 review profile

**Status:** Complete. Immutable AMD64/ARM64 `0.5.1` was published, deployed, runtime-verified, browser-accepted, and squash-merged through PR #14 at `dd46a08`.

- Pin the OWASP Kubernetes Top 10:2025 source to an exact upstream commit.
- Label each category as direct, partial, or cluster-context-required coverage.
- Add bounded manifest-local signals for authorization, secrets, admission policy, segmentation, exposure, cloud credentials, and ServiceAccount authentication.
- Keep category coverage distinct from finding severity and explicitly avoid compliance, score, pass, or cluster-state claims.
- Preserve General YAML mode without Kubernetes or OWASP findings and retain the no-backend, no-cluster-access boundary.

See [Milestone 037](docs/milestones/milestone-037-owasp-kubernetes-profile.md).

#### Milestone 038 — Formatting preview

**Status:** Complete. Immutable `0.6.0` was published, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #16 at `4fed28c`.

- Replace immediate formatting mutation with a browser-local, line-oriented preview.
- Keep the editor unchanged until explicit Apply and preserve it through Cancel or Escape.
- Show before/after line numbers, added and removed lines, and normalization details.
- Retain the invalid-YAML path to Validation without attempting speculative repair.
- Bound expensive alignment work while leaving broader large-file guarantees for a later milestone.
- Preserve both inspection modes and the no-backend, no-cluster-access trust boundary.

See [Milestone 038](docs/milestones/milestone-038-formatting-preview.md).

#### Milestone 039 — Browser-local Markdown analysis reports

**Status:** Complete. Immutable `0.7.0` was deployed, runtime-verified, live browser-accepted, and merged through PR #18 at `1e0c525`.

- Generate a deterministic Markdown report from the current browser-local analysis snapshot.
- Let the operator review the report before explicitly copying it or downloading it as a `.md` file.
- Include mode-appropriate summaries, diagnostics, findings, schema results, recommendations, and boundary language without embedding the complete source YAML.
- Treat clipboard copy and local download as explicit trust-boundary crossings.
- Preserve editor contents, unsaved-state tracking, both inspection modes, and the no-backend, no-cluster-access boundary.
- Published the separately approved AMD64/ARM64 `0.7.0` image at immutable OCI index `sha256:f9f5939910382911b23e78609ea5690e617e2a446c3dd707da2c1c6852a8a6d2` in workflow run `34886290349`.
- Deployed the separately approved Deployment-only update with matching `0.7.0` labels and the immutable OCI index.
- Verified one Ready Pod with zero restarts, a matching runtime ImageID, a ready EndpointSlice, HTTP 200 health and page responses, strict security headers, and the complete live browser workflow.
- Completed final review and merged PR #18 at `1e0c525`; all three post-merge workflows passed.

See [Milestone 039](docs/milestones/milestone-039-browser-local-markdown-reports.md).

#### Milestone 040 — Validation result filters

**Status:** Complete. Immutable `0.8.0` was published, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #20 at `6fa5092`.

- Filter existing Validation entries by All, Errors, Warnings, Notes, or Valid with current counts.
- Preserve section and result order, hide empty filtered sections, and distinguish filtered-empty results from the complete analysis.
- Keep the tab badge, overall status, OWASP review profile, and Markdown reports based on the complete unfiltered analysis.
- Preserve filters through edits while resetting them at inspection-mode and input-replacement boundaries.
- Keep all filter state ephemeral and browser-local without adding storage, backend processing, cluster access, or credentials.
- Deployed the approved Deployment-only update and verified one Ready Pod with zero restarts, a matching runtime ImageID, one ready endpoint, HTTP 200 health and page responses, strict security headers, and the complete live filter workflow.

See [Milestone 040](docs/milestones/milestone-040-validation-result-filters.md).

#### Milestone 041 — Browser-local YAML tree search

**Status:** Complete. Immutable `0.9.0` was published, digest-pinned, deployed, runtime-verified, live browser-accepted, merged through PR #22 at `0f3d44e`, and cleaned up.

- Search keys, scalar values, and canonical paths with case-insensitive literal matching.
- Count matches once per node and navigate deterministically with wrapping Previous and Next actions.
- Expand matching ancestors and distinguish all matches from the active match.
- Preserve accessible keyboard, focus, disclosure, and live-status behavior.
- Recompute through edits and formatting while resetting at explicit mode and input-replacement boundaries.
- Keep search ephemeral and independent of analysis, Validation filters, reports, storage, backend processing, network access, credentials, and cluster state.
- Deployed the approved Deployment-only update and verified one Ready Pod with zero restarts, an exact runtime OCI index match, one ready endpoint, HTTP 200 health and page responses, strict security headers, and the complete live Tree-search workflow.

See [Milestone 041](docs/milestones/milestone-041-browser-local-tree-search.md).

#### Milestone 042 — Safe browser-local YAML file drop

**Status:** Local implementation and automated verification complete on `codex/milestone-042-safe-yaml-drop`; publication has not been authorized.

- Accept one local `.yaml` or `.yml` file through a visible editor drop target.
- Preserve keyboard-equivalent Open file behavior and announce drag, rejection, cancellation, success, and read-failure states.
- Protect dropped-file, Open file, and sample replacement behind one unsaved-change confirmation boundary.
- Preserve mode and active tab while resetting Validation filtering and Tree search and invalidating a prepared report after successful replacement.
- Prevent browser navigation for misplaced file drops and preserve all source and derived state after rejection, cancellation, or read failure.
- Keep file contents, basename, and transient drag state in browser memory without adding upload, persistence, telemetry, backend, Kubernetes API, credential, or cluster-mutation paths.

See [Milestone 042](docs/milestones/milestone-042-safe-browser-local-yaml-file-drop.md).

- Later increments: display preferences, additional export formats, and bounded large-file processing.

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
