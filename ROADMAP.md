# The Foundry Initiative Roadmap

**Last updated:** 2026-09-19

The roadmap favors small, demonstrable outcomes over large unfinished plans. It describes direction and sequencing; detailed implementation evidence belongs in `docs/milestones`, and the live system state belongs in `docs/project-status.md`.

## Current position

The active workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. Milestones 001-030 and 032-062 are complete, merged, closed, synchronized, and cleaned up. Milestone 062 completed its approved deterministic incident-copilot demonstration through implementation PR #63 and closeout PR #64. Restaurant API `0.7.0` runs as three replicas alongside lightweight Prometheus, Kubernetes Metrics Server, Grafana, bounded rule evaluation, and Forge YAML Workbench. NVMe-backed Prometheus and Grafana use retained local storage with tested persistence and recovery procedures; the Workbench is intentionally stateless and performs analysis in the browser. The repository-owned GitHub Wiki front door is live without transferring authority away from repository documentation. ForgeOps implements and has live-validated the accepted bounded, read-only snapshot contract with offline fixtures, a deny-by-default runner, deterministic evidence and comparison JSON contracts, strict offline validation for explicitly selected saved artifacts, deterministic offline comparison and replay, a bounded synthetic scenario corpus, explicit local execution identity, exact-byte integrity, validated runbook knowledge, grounded deterministic mapping, strict mapping validation, deterministic structured and operator incident briefs, exact brief replay, and adversarial trust-boundary evaluation. Model and retrieval integration remain deferred because Milestone 062 identified no concrete operator question unmet by the deterministic brief.

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

**Status:** Complete. Immutable `0.10.0` is verified for AMD64 and ARM64, digest-pinned, deployed as generation 14, live browser-accepted, merged through PR #23 at `020d5e7`, and cleaned up.

- Accept one local `.yaml` or `.yml` file through a visible editor drop target.
- Preserve keyboard-equivalent Open file behavior and announce drag, rejection, cancellation, success, and read-failure states.
- Protect dropped-file, Open file, and sample replacement behind one unsaved-change confirmation boundary.
- Preserve mode and active tab while resetting Validation filtering and Tree search and invalidating a prepared report after successful replacement.
- Prevent browser navigation for misplaced file drops and preserve all source and derived state after rejection, cancellation, or read failure.
- Keep file contents, basename, and transient drag state in browser memory without adding upload, persistence, telemetry, backend, Kubernetes API, credential, or cluster-mutation paths.

See [Milestone 042](docs/milestones/milestone-042-safe-browser-local-yaml-file-drop.md).

- Workbench later increments: display preferences, additional export formats, and bounded large-file processing.

#### Milestone 043 — Curated documentation front door

**Status:** Complete. The Wiki is live at commit `0a945b4`; browser acceptance, merge, closeout, and branch cleanup are complete.

- Maintain a concise Wiki Home and custom sidebar as exact derivatives of reviewed source under `docs/wiki`.
- Route recruiters, technical reviewers, operators, and learners to authoritative repository documents without copying volatile status, procedures, or evidence.
- Validate Wiki structure, accessibility-oriented headings and link text, same-repository targets, stable-content boundaries, and byte-for-byte publication.
- Restrict Restaurant API image publication on `main` to Restaurant API source changes while preserving version-tag and manual publication.
- Keep the repository authoritative and collaborator-only Wiki editing intact.

See [Milestone 043](docs/milestones/milestone-043-curated-documentation-front-door.md).

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

**Status:** In progress — deterministic incident-copilot baseline and demonstration complete; v1-readiness planning is next

Evolve the rules-based `/analyze` endpoint into a grounded Kubernetes incident copilot.

### Milestone 044 — Read-only health snapshot design

**Status:** Complete. Design, publication, read-only live feasibility, and merge completed through PR #27 at `c467468`.

- Define a separate local ForgeOps command rather than extending the mixed read/write `forge.ps1` dispatcher.
- Require an explicit kubeconfig and exact context before any collection.
- Limit collection to named SignalForge nodes, workloads, EndpointSlices, Metrics APIService availability, and explicitly configured application endpoints.
- Normalize evidence before rendering stable terminal and Markdown results.
- Fail closed on context mismatch or incomplete required evidence and preserve `UNKNOWN` instead of assuming health.
- Exclude logs, Events, Secrets, ConfigMaps, broad discovery, cluster mutation, remediation, AI reasoning, and deployment.
- Define offline fixture coverage, command allowlisting, redaction, timeouts, exit codes, and a separately approved read-only feasibility check.
- Confirm the contract against the live four-node, five-Deployment SignalForge baseline and five allowlisted HTTP endpoints without mutation or restricted-data access.

See [Milestone 044](docs/milestones/milestone-044-forgeops-read-only-health-snapshot-design.md).

### Milestone 045 — Deterministic read-only snapshot

**Status:** Complete. Implementation, publication, CI, read-only live acceptance, PR readiness, and merge completed through PR #29 at `3e9851d`.

- Implement the accepted local `forgeops snapshot` interface.
- Preserve exact kubeconfig and context preflight and fail closed before collection.
- Reduce responses to selected evidence before deterministic evaluation.
- Render equivalent terminal and Markdown checks with stable ordering and exit codes.
- Enforce fixed target mappings, bounded subprocess and HTTP behavior, redaction, and no mutation.
- Cover the healthy baseline and failure boundaries with synthetic offline fixtures and dedicated CI.
- Preserve `foundry-check` and avoid any package registry, image, manifest, deployment, or Wiki change.
- Confirm the exact published tree against the live four-node baseline with 33 passing deterministic checks and exit code `0`.

See [Milestone 045](docs/milestones/milestone-045-forgeops-deterministic-read-only-snapshot.md) and the [ForgeOps snapshot runbook](docs/runbooks/forgeops-snapshot.md).

### Milestone 046 — Deterministic JSON evidence contract

**Status:** Complete. Implementation PR #31 merged at `4715628`; closeout PR #32 merged at `66bae40`; Gate 10 cleanup removed both Milestone 046 branches locally and remotely.

- Add `--format json` without adding a new command or collection path.
- Serialize only the evaluated, redacted `forgeops.snapshot/v1alpha1` model rather than raw Kubernetes or HTTP responses.
- Preserve ordered checks, `PASS`/`WARN`/`FAIL`/`UNKNOWN` semantics, summary counts, overall status, and exit code across all three renderers.
- Prove deterministic serialization with a fixed golden artifact and cover mixed-status precedence, semantic parity, and redaction offline.
- Retain the exact kubeconfig, context, resource, endpoint, timeout, size, and no-mutation boundaries from Milestone 045.
- Exclude replay, comparison, history, signing, new telemetry, recommendations, AI reasoning, package publication, deployment, and cluster mutation.
- Confirm the exact published tree against SignalForge with 33 passing JSON checks, five explicit HTTP checks, verified redaction, and exit code `0` without cluster mutation.

See [Milestone 046](docs/milestones/milestone-046-forgeops-json-evidence-contract.md).

### Milestone 047 — Deterministic offline evidence validation

**Status:** Complete. Implementation PR #33 merged at `a92b4b8`; closeout PR #34 merged at `2ebaa90`; Gate 10 cleanup removed both Milestone 047 branches locally and remotely.

- Add `forgeops evidence validate --input <explicit-file>` as a separate offline consumer of the Milestone 046 JSON artifact.
- Read only one explicitly selected regular file, enforce a 1 MiB limit, and require UTF-8 JSON without duplicate keys or non-standard numeric constants.
- Validate the exact supported schema, ordered fields, value types, timestamps, unique check identifiers, limitations, and summary semantics.
- Recalculate counts, overall-status precedence, and contained exit code rather than trusting serialized summary values.
- Return validator success for a valid `WARN`, `FAIL`, or `UNKNOWN` artifact without describing the contained cluster state as healthy.
- Keep artifact validation separate from collection: no kubeconfig, kubectl, HTTP, network, discovery, storage, recommendation, AI, or mutation authority.
- Exclude comparison, replay, history, repair, signing, runbook mapping, diagnosis, recommendation, and AI reasoning.
- Preserve the validated in-memory representation as the future input seam for separately planned comparison or reasoning.

See [Milestone 047](docs/milestones/milestone-047-forgeops-offline-evidence-validation.md).

### Milestone 048 — Deterministic offline evidence comparison

**Status:** Complete and cleaned up. Implementation PR #35 merged at `ad05786`; closeout PR #36 merged at `9055ef8`; Gate 10 removed both Milestone 048 branches locally and remotely. Package release, deployment, and live acceptance were explicitly closed as not applicable.

- Add `forgeops evidence compare --before <file> --after <file>` as a second consumer of the Milestone 047 validation seam.
- Validate both explicitly selected artifacts before producing any comparison output.
- Match checks by identifier and report additions, removals, status transitions, and same-status evidence changes in stable identifier order.
- Display but do not classify collection timestamps as evidence changes; reject an `after` artifact that predates `before`.
- Use comparison exit code `0` for equivalent valid artifacts, `1` for valid artifacts with differences, and `2` for invalid input or chronology.
- Preserve an immutable in-memory comparison model without introducing a serialized comparison schema.
- Keep comparison separate from collection, persistence, replay, diagnosis, recommendation, AI reasoning, remediation, and mutation.
- Exclude package publication, image, manifest, deployment, live-cluster acceptance, and Wiki changes.

See [Milestone 048](docs/milestones/milestone-048-forgeops-offline-evidence-comparison.md).

### Milestone 049 — Deterministic JSON comparison contract

**Status:** Complete and cleaned up. Implementation PR #37 merged at `972e611`; closeout PR #38 merged at `38bf1d8`; Gate 10 removed both Milestone 049 branches locally and remotely. Package/image release, deployment, and live acceptance were explicitly closed as not applicable.

- Add `--format text|json` to the existing offline comparison command while keeping text as the default.
- Serialize only the immutable `EvidenceComparison` model as `forgeops.comparison/v1alpha1`.
- Preserve timestamps, contained statuses, counts, check identifiers, delta kinds, before/after statuses, changed-field names, and comparison exit semantics.
- Prove fixed field order, stable identifier order, byte-repeatability, text/JSON parity, explicit null behavior, and disclosure minimization through offline tests and a golden fixture.
- Omit artifact paths, observations, expected or observed values, sources, errors, and complete input artifacts.
- Keep the renderer unable to read files, collect evidence, invoke a runner, contact a network, persist output automatically, infer causes, recommend actions, or mutate state.
- Exclude a comparison loader, scenario replay, history, provenance claims, compatibility negotiation, runbook mapping, AI reasoning, package publication, image, manifest, deployment, live acceptance, and Wiki changes.

See [Milestone 049](docs/milestones/milestone-049-forgeops-json-comparison-contract.md).

### Milestone 050 — Bounded synthetic scenario corpus

**Status:** Complete, merged, closed, synchronized, and cleaned up. Implementation PR #39 merged at `090a47f`; closeout PR #40 merged at `59cad31`. Gates 4-6 were explicitly closed as not applicable.

- Add five focused synthetic before/after evidence pairs covering timestamp-only stability, a Pod-restart warning, a routing regression, incomplete evidence, and routing recovery.
- Validate every artifact through the existing strict `forgeops.snapshot/v1alpha1` loader.
- Compare every pair through the existing immutable comparison seam and prove exact byte-stable `forgeops.comparison/v1alpha1` output.
- Preserve the distinction between contained health and comparison execution, including comparison exit `1` for a valid recovery.
- Keep the corpus disclosure-minimized and explicitly separate from captured SignalForge evidence, current-health claims, training data, provenance, diagnosis, recommendation, remediation, and mutation.
- Add no production model, schema, CLI, package-version, workflow, image, manifest, deployment, live-acceptance, or Wiki change.

See [Milestone 050](docs/milestones/milestone-050-forgeops-synthetic-scenario-corpus.md).

### Milestone 051 — Trustworthy execution provenance

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #41 merged at `e5e2a08`; closeout PR #42 merged at `fd81876`. Gates 4-6 were explicitly closed as not applicable.

- Add `forgeops provenance` to expose the distribution, module version, loaded
  module path, Python executable, execution mode, and recorded source.
- Detect version disagreement, invalid declared source mode, missing editable
  source, and temporary-directory editable installations.
- Replace the global editable-install recommendation with an isolated normal
  operator install and a repository-owned source launcher.
- Consolidate architecture, commands, evidence flow, exit semantics, and trust
  boundaries into one current operator and learning guide.
- Keep Milestones 044-050 intact as chronological evidence.
- Add no collection, network, evidence-integrity, replay, reasoning, mutation,
  deployment, or cluster authority.

See [Milestone 051](docs/milestones/milestone-051-forgeops-execution-provenance.md)
and the [ForgeOps operator and learning guide](docs/guides/forgeops-operator-learning-guide.md).

### Milestone 052 — Deterministic evidence integrity records

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #43 merged at `b4f42c2`; closeout PR #44 merged at `801f8ce`. Gates 4-6 were closed as not applicable.

- Add `forgeops evidence integrity create --input <file>` to render a
  deterministic `forgeops.integrity/v1alpha1` record for exact validated bytes.
- Add `forgeops evidence integrity verify --input <file> --record <file>` with
  separate match, mismatch, and invalid-input exits.
- Bind the record to evidence schema, collection timestamp, context, byte
  length, and SHA-256 digest without exposing artifact paths or evidence values.
- Read and validate the evidence once before hashing those same bytes.
- Require separate trusted retention for a meaningful later verification.
- Make no authorship, authenticity, signing, trusted-time, attestation, or
  chain-of-custody claim.
- Add no collection, network, replay, reasoning, mutation, deployment, or
  cluster authority.

See [Milestone 052](docs/milestones/milestone-052-forgeops-evidence-integrity.md).

### Milestone 053 — Bounded offline scenario replay

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #45 merged at `6900aa9`; closeout PR #46 merged at `c8ad7b6`. Gate 10 removed both Milestone 053 branches locally and remotely. Gates 4-6 were closed as not applicable.

- Add `forgeops scenario replay --before <file> --after <file> --expected <file>`.
- Strictly load the existing `forgeops.comparison/v1alpha1` contract with a
  256 KiB limit, duplicate-key rejection, exact fields, supported values,
  sorted unique deltas, kind-specific shapes, and recalculated summary counts.
- Reuse the existing strict evidence loader and deterministic comparison seam.
- Return replay exit `0` for an expectation match, `1` for a valid mismatch,
  and `2` for invalid evidence, expectation, or chronology.
- Keep replay success distinct from contained health and comparison exits.
- Require all three explicit paths; do not discover directories or scenarios.
- Add no collection, network, retention, runbook mapping, diagnosis,
  recommendation, AI reasoning, remediation, deployment, or cluster authority.

See [Milestone 053](docs/milestones/milestone-053-forgeops-scenario-replay.md).

### Milestone 054 — Validated runbook knowledge catalog

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #47 merged at `a59dec9`; closeout PR #48 merged at `a4fbf0d`. Gate 10 removed both Milestone 054 branches locally and remotely. Gates 4-6 were closed as not applicable.

- Add `forgeops runbook catalog validate --input <file>` as a separate offline
  validator for `forgeops.runbook-catalog/v1alpha1`.
- Catalog stable runbook IDs, repository-relative Markdown targets, exact
  section headings, and bounded signal selectors.
- Enforce strict fields, ordering, enumerations, safe paths, duplicate-key
  rejection, UTF-8 JSON, and a 256 KiB input limit.
- Prove every canonical runbook path and section exists in the repository.
- Add no runbook selection, applicability claim, diagnosis, recommendation,
  model invocation, remediation, deployment, or cluster authority.

See [Milestone 054](docs/milestones/milestone-054-forgeops-runbook-catalog.md).

### Milestone 055 — Deterministic grounded runbook mapping

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #49 merged at `113e629`; closeout PR #50 merged at `5e5bcde`. Gate 10 removed both Milestone 055 branches locally and remotely. Gates 4-6 were closed as not applicable.

- Add `forgeops runbook map --comparison <file> --catalog <file>` with text and
  JSON output.
- Validate both explicit inputs before evaluating catalog rules.
- Match only check identifier, delta kind, and after status; cite every matched
  delta and exact repository runbook section.
- Serialize the bounded `forgeops.runbook-mapping/v1alpha1` contract.
- Return `0` when all deltas are mapped, `1` when valid deltas remain unmapped,
  and `2` for invalid input.
- Keep mapping exit separate from evidence health and comparison exit.
- Add no causal inference, diagnosis, recommendation, model invocation,
  remediation, deployment, or cluster authority.

See [Milestone 055](docs/milestones/milestone-055-forgeops-runbook-mapping.md).

### Milestone 056 — Bounded incident-reasoning design and evaluation

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #51 merged at `04b686a`; closeout PR #52 merged at `548b63e`. Gate 10 removed both Milestone 056 branches locally and remotely. Gates 4-6 were closed as not applicable.

- Define the proposed explicit incident-brief inputs, disclosure-bounded
  output, evidence citations, uncertainty rules, and authority limitations.
- Define `STABLE`, `DEGRADED`, `INCOMPLETE`, and `RECOVERED` only as summaries
  of the supplied comparison window.
- Add a five-case `forgeops.incident-evaluation/v1alpha1` synthetic corpus.
- Recalculate expected deltas and runbook mappings through current production
  seams in offline tests.
- Require every future factual statement to trace to validated comparison or
  mapping fields and forbid unsupported cause, current-health, severity, and
  remediation claims.
- Add no incident command, mapping loader, model, retrieval, diagnosis,
  recommendation, deployment, or cluster authority.

See [Milestone 056](docs/milestones/milestone-056-forgeops-incident-reasoning-design.md)
and the [bounded incident-reasoning design](docs/design/forgeops-bounded-incident-reasoning.md).

### Milestone 057 — Strict runbook-mapping artifact validation

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #54 merged at `35c6e87`; grouped closeout PR #59 recorded final acceptance and Gate 10 cleanup.

- Add `forgeops runbook mapping validate --input <file>`.
- Strictly load the existing `forgeops.runbook-mapping/v1alpha1` contract.
- Keep validation success separate from contained mapping completeness.
- Add no incident state, briefing, diagnosis, model, network, or cluster authority.

See [Milestone 057](docs/milestones/milestone-057-forgeops-runbook-mapping-validation.md).

### Milestone 058 — Deterministic structured incident brief

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #55 merged at `67d0d41`; grouped closeout PR #59 recorded final acceptance and Gate 10 cleanup.

- Add JSON-only `forgeops incident brief` for explicit comparison and mapping files.
- Cross-check both validated artifacts before rendering.
- Add the neutral `CHANGED` state so the classifier is total without making a health claim.
- Preserve citations, unmapped deltas, uncertainty, and fixed authority limitations.
- Add no model, retrieval, diagnosis, recommendation, network, or cluster authority.

See [Milestone 058](docs/milestones/milestone-058-forgeops-structured-incident-brief.md).

### Milestone 059 — Exact incident-brief replay and evaluation

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #56 merged at `e2c3134`; grouped closeout PR #59 recorded final acceptance and Gate 10 cleanup.

- Strictly load `forgeops.incident-brief/v1alpha1` expectations.
- Add explicit comparison, mapping, and expected-brief replay.
- Store exact expected briefs for all five synthetic scenarios.
- Keep replay success separate from the contained incident state.
- Add no model, diagnosis, network, deployment, or cluster authority.

See [Milestone 059](docs/milestones/milestone-059-forgeops-incident-brief-replay.md).

### Milestone 060 — Deterministic operator-facing incident brief

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #57 merged at `f3c63ba`; grouped closeout PR #59 recorded final acceptance and Gate 10 cleanup.

- Add a fixed human-readable renderer over the accepted structured brief.
- Preserve parity with JSON, visible unmapped deltas, uncertainty, and limitations.
- Label runbook references as informational catalog-rule matches.
- Add no prose generation, model, diagnosis, recommendation, or operational authority.

See [Milestone 060](docs/milestones/milestone-060-forgeops-operator-incident-brief.md).

### Milestone 061 — Adversarial evaluation and model-readiness decision

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR #58 merged at `9f3d8f1`; grouped closeout PR #59 recorded final acceptance and Gate 10 cleanup.

- Exercise nine synthetic adversarial trust-boundary cases through production seams.
- Prove neutral, incomplete, degraded, recovery, mapping-gap, and rejection behavior.
- Record explicitly that structural validation is not artifact authenticity.
- Defer model and retrieval integration until an end-to-end demonstration identifies a measurable unmet need.
- Add no runtime command, dependency, network, deployment, or cluster authority.

See [Milestone 061](docs/milestones/milestone-061-forgeops-adversarial-evaluation.md)
and the [model-readiness decision](docs/design/forgeops-model-readiness-decision.md).

### Milestone 062 — Deterministic incident-copilot demonstration

**Status:** Complete, merged, synchronized, and cleaned up. Implementation PR
#63 merged at `6e7e580`; closeout PR #64 merged at `5619a5f`.

- Demonstrate the current evidence-to-brief path without adding a new command,
  model, dependency, or operational authority.
- Keep a reviewed synthetic routing regression separate from two bounded live
  read-only snapshots.
- Accept a truthful `STABLE` live result rather than injecting a failure.
- Preserve execution provenance, validation, integrity limitations, distinct
  exit domains, grounded catalog-rule matches, uncertainty, and human review.
- Record whether the deterministic brief leaves a concrete operator question
  unmet before reconsidering model or retrieval work.

See [Milestone 062](docs/milestones/milestone-062-forgeops-incident-copilot-demonstration.md)
and the [demonstration guide](docs/guides/forgeops-incident-copilot-demonstration.md).

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
