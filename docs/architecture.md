# SignalForge Architecture

**Last updated:** 2026-09-11

This document describes the current architecture of the active Foundry Initiative workstream. Detailed implementation history lives under `docs/milestones`, while operating procedures live under `docs/runbooks`.

## System purpose

SignalForge is a four-node Raspberry Pi Kubernetes lab for practicing cloud-native application delivery, release engineering, observability, troubleshooting, and eventually AI-assisted operations.

The primary workload is the SignalForge Restaurant API, a small FastAPI service that makes infrastructure behavior visible through health endpoints, runtime metadata, application metrics, and intentionally simple operational workflows. Forge YAML Workbench is a separate stateless browser application for inspecting Kubernetes YAML without granting it cluster access.

## Current topology

```mermaid
flowchart TD
    Client["Laptop or client"] --> NodePort["NodePort 30080"]
    Client --> WorkbenchPort["NodePort 30081"]
    NodePort --> API["Restaurant API Pods (3)"]
    WorkbenchPort --> Workbench["YAML Workbench (1)"]
    Prometheus["Prometheus (1)"] -->|scrape /metrics| API
    Operator["Operator kubectl"] -->|top request| APIServer["Kubernetes API server"]
    APIServer --> MetricsServer["Metrics Server (1)"]
    MetricsServer -->|verified TLS on 10250| Kubelets["Kubelets (4)"]
    Actions["GitHub Actions"] -->|publish ARM64 image| Registry["Docker Hub"]
    Registry -->|versioned image| API
    Registry -->|digest-pinned image| Workbench
```

### Kubernetes platform

- Cluster: SignalForge Raspberry Pi Kubernetes cluster
- Control plane: `forge-head`
- Worker nodes: `forge-node-01`, `forge-node-02`, and `forge-node-03`
- Workload architecture: `linux/arm64`
- Operator access: laptop-based `kubectl`

### Restaurant API

- Source: `apps/restaurant-api`
- Namespace: `forge-restaurant`
- Deployment: `restaurant-api`
- Replicas: 3
- Current release: `0.7.0`
- Internal access: ClusterIP Service `restaurant-api`
- External lab access: NodePort Service on port `30080`
- Runtime configuration: ConfigMap `restaurant-api-config`
- Health signals: `/health` and `/ready`
- Application metrics: `/metrics`
- Deployment strategy: rolling update with readiness and liveness probes

### Forge YAML Workbench

- Source: `apps/forge-yaml-workbench`
- Manifests: `k8s/forge-yaml-workbench`
- Namespace: `forge-tools`
- Deployment: one stateless replica using release `0.1.1`
- Access: private-lab NodePort `30081`
- Runtime: unprivileged NGINX on container port `8080`
- Processing: YAML parsing, formatting, summaries and bounded findings run entirely in the browser
- Identity: no RBAC, Kubernetes API access, or mounted ServiceAccount token
- Security: restricted Pod Security labels, non-root execution, RuntimeDefault seccomp, read-only root filesystem, dropped capabilities, and bounded writable `/tmp`
- Delivery: guarded version tags publish AMD64 and ARM64 images; the Deployment pins both version and OCI index digest

### Metrics collection

- Manifests: `k8s/prometheus`
- Namespace: `forge-observability`
- Collector: one Prometheus replica using `prom/prometheus:v3.13.2`
- Discovery: Kubernetes Pod discovery limited to `forge-restaurant`
- Authorization: namespace-scoped Role granting only `get`, `list`, and `watch` on Pods
- Scrape model: each Restaurant API Pod is scraped independently every 30 seconds
- Access: ClusterIP Service and temporary `kubectl port-forward`
- Storage: retained 30 GiB local PV on the head NVMe, 30-day retention, and a 24 GB cap

Prometheus remains deliberately lightweight. Grafana is deployed as a separate visualization layer; Alertmanager, node-exporter, kube-state-metrics, and the Prometheus Operator are not installed.

### Approved persistent-storage target

Milestone 025 selected a static Kubernetes `local` PersistentVolume backed by a dedicated ext4 partition on the `forge-head` NVMe. The target design uses a non-default `WaitForFirstConsumer` StorageClass, a 30 GiB `ReadWriteOnce` claim, `Retain` reclaim policy, exact PV node affinity for `forge-head`, and Prometheus retention of 30 days or 24 GB.

The host-storage portion is prepared. Physical inventory identified the installed device as a 512 GB Samsung SSD 950 PRO, and its first 32 GiB partition is an ext4 filesystem mounted by UUID at `/mnt/signalforge-prometheus`. The `data` directory exists only on that mounted filesystem and is owned by Prometheus's verified `65534:65534` runtime identity.

The cutover is live. Prometheus uses the bound local claim on `forge-head`. Pod-replacement persistence and six-block off-node backup/restore analysis passed; port-forward verification and storage rollback/return also passed.

The design provides persistence across Pod replacement, not high availability. If `forge-head` is unavailable, Prometheus remains unavailable because the local volume cannot move to another node. Weekly cold backups will be copied off the head node so an NVMe failure does not make the node-local copy the only recovery source.

### Kubernetes resource metrics

- Manifests: `k8s/metrics-server`
- Namespace: `kube-system`
- Collector: one Metrics Server replica using `registry.k8s.io/metrics-server/metrics-server:v0.9.0`
- API: aggregated `metrics.k8s.io/v1beta1`
- Collection: current CPU and memory samples every 15 seconds
- Kubelet addressing: InternalIP first
- Kubelet trust: Kubernetes service-account CA
- Operator access: `kubectl top nodes` and `kubectl top pods`
- Observed footprint: 4m CPU and 21 MiB memory

Every kubelet uses a Kubernetes-CA-signed serving certificate containing its hostname and InternalIP as SANs. Metrics Server explicitly supplies `--kubelet-certificate-authority` and does not use `--kubelet-insecure-tls`.

Metrics Server and Prometheus have different responsibilities. Metrics Server retains only the latest resource samples needed by Kubernetes operations and autoscaling. Prometheus retains application time series for querying behavior over time.

## Application metric design

The Restaurant API publishes:

- application metadata and feature-state gauges
- a request counter labeled by method, matched route, status, and traffic type
- a request-duration histogram that can be aggregated across all three replicas

Kubernetes probes and Prometheus scrapes are classified as `traffic="synthetic"`. Other routes use `traffic="application"`. Unmatched URLs are normalized to `path="unmatched"` so arbitrary paths cannot create unbounded time-series cardinality.

Baseline queries are maintained in `docs/observability/prometheus-queries.md`.

## Delivery and validation flow

Milestone 029's limited-alerting design is accepted and merged. Milestone 030's canonical rules passed all 19 pinned-promtool scenarios and are now loaded by the existing Prometheus evaluator through the existing read-only `/etc/prometheus` ConfigMap mount. Activation changed only the ConfigMap and restarted only Prometheus after an exact-baseline check, dry-run, reviewed diff, recovery capture and explicit approval. Immediate and independent checks confirmed an exact live/repository match, three healthy targets, and two rules with healthy inactive state. Grafana unified alerting remains disabled, and no Alertmanager, receiver or notification path is configured; evaluator failure remains an uncovered condition.

1. Application and infrastructure changes are developed in Git.
2. Restaurant API tests run through GitHub Actions.
3. Kubernetes manifests are checked by the repository validator and `promtool` where appropriate.
4. GitHub Actions builds the Restaurant API ARM64 image and Workbench AMD64/ARM64 image.
5. Guarded version tags publish versioned release images to Docker Hub.
6. PowerShell helpers apply the manifests and wait for Kubernetes rollouts.
7. Smoke tests, Prometheus target checks, and Metrics API checks validate the live deployment.

## Repository organization

- `apps/restaurant-api` contains the FastAPI source, container definition, dependencies, and tests.
- `apps/forge-yaml-workbench` contains the browser application, analyzer, tests, and unprivileged web container.
- `k8s/fastapi-restaurant` contains the Restaurant API Kubernetes resources.
- `k8s/prometheus` contains the lightweight metrics-collection resources.
- `k8s/metrics-server` contains the Kubernetes resource-metrics API resources.
- `k8s/forge-yaml-workbench` contains the restricted namespace, hardened Deployment, NodePort Service, and operating notes.
- `scripts` contains developer, deployment, smoke-test, and validation helpers.
- `.github/workflows` contains application CI, manifest validation, and ARM64 image publishing.
- `docs/milestones` preserves chronological implementation evidence.
- `docs/observability` contains reusable metrics queries and guidance.
- `docs/runbooks` contains operator procedures and recovery steps.

## Architectural principles

- Prefer small, demonstrable increments over broad platform installations.
- Keep configuration outside application source code.
- Pin release and infrastructure image versions.
- Apply least-privilege Kubernetes access.
- Prefer trusted serving certificates over disabling TLS validation.
- Protect metric label cardinality.
- Automate repeatable validation and preserve manual troubleshooting skills.
- Keep externally reachable services intentional; Prometheus remains ClusterIP-only.
- Record temporary limitations instead of hiding them.

## Current constraints

- Prometheus storage is node-local; head-node or NVMe failure requires recovery. Weekly backups remain manual, and full service-restoration timing has not been measured.
- NodePort is appropriate for the private lab but is not the long-term ingress design.
- Metrics Server provides current CPU and memory samples but no historical resource-metrics store.
- The upstream APIService uses `insecureSkipTLSVerify` for the API server-to-Metrics Server connection because the serving certificate is generated dynamically. This is separate from the secured Metrics Server-to-kubelet path.
- Kubelet serving-certificate rotation requests require deliberate operator review and approval.
- Workbench analysis is not complete Kubernetes schema or admission validation; NodePort `30081` is private-lab HTTP exposure.

## Expected evolution

Potential next architecture steps include:

1. Observe naturally occurring limited-alert behavior before designing notification delivery.
2. Continue the demonstrated Prometheus and Grafana backup cadence.
3. Introduce Ingress and TLS for cleaner private-lab access when selected as a bounded milestone.
4. Evaluate Loki and OpenTelemetry only for defined logging or tracing questions.
5. Evolve the rules-based `/analyze` endpoint into the ForgeOps AI-assisted incident copilot.

## Decision records

Milestone documents currently serve as the chronological record of context, decisions, implementation, validation, and lessons. Larger cross-cutting decisions can later be promoted into dedicated records under `docs/decisions` when that additional structure provides value.

