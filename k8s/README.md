# Kubernetes Manifests

SignalForge Kubernetes resources are grouped by workload.

## Restaurant API

Path: `k8s/fastapi-restaurant`

This directory contains the `forge-restaurant` namespace, Restaurant API configuration, Deployment, internal Service, and NodePort Service.

## Lightweight Prometheus

Path: `k8s/prometheus`

This directory contains the `forge-observability` namespace, least-privilege Pod-discovery RBAC, Prometheus configuration, Deployment, and internal Service.

## Kubernetes Metrics Server

Path: `k8s/metrics-server`

This directory contains the pinned Metrics Server v0.9.0 workload, upstream RBAC, internal Service, and aggregated API registration. The deployment validates every kubelet serving certificate with the Kubernetes service-account CA and does not use `--kubelet-insecure-tls`.

## Forge YAML Workbench

Path: `k8s/forge-yaml-workbench`

This directory contains the restricted `forge-tools` namespace, hardened stateless Workbench Deployment, and NodePort Service on `30081`. The live workload and tracked Deployment use accepted immutable `0.10.0`, including safe browser-local YAML file drop and the earlier corrected finding-navigation scrolling. The Workbench has no Kubernetes API identity or mounted ServiceAccount token and processes YAML only in the browser.

## Service Pulse

Path: `k8s/service-pulse`

This directory contains the restricted `forge-pulse` namespace, one live probe and one live board Deployment, and their internal ClusterIP Services. Both pin the published `0.1.1` OCI digest. The board is accessible by port-forward only from outside the cluster. See its README for live acceptance evidence, change review, and scoped rollback.

## Grafana and central logging

Paths: `k8s/grafana` and `k8s/central-logging`

Grafana provides the existing Prometheus dashboards and a provisioned Loki datasource. Alloy reads Service Pulse Pod logs with namespace-scoped permissions and sends them to a private, persistent Loki instance. The [central logging rollout record](central-logging/README.md) documents observed ingestion, Grafana queries, and log retrieval after a probe Pod replacement. It also records the remaining Loki persistence, retention, and recovery checks. Follow the reviewed per-resource procedure; do not apply the central logging directory wholesale or rerun its storage preparation.

## Istio learning lab

Path: `k8s/istio-lab`

The [guided lab](istio-lab/README.md) uses an isolated namespace, two versions
of a small HTTP service, and one client to explore sidecar injection, traffic
shifting, a scoped HTTP fault, diagnosis, and repair. The client makes one
request every 15 seconds so the Grafana panels remain useful between lessons.
Its route files represent alternative states of the same VirtualService; apply
them one at a time. Keep the healthy meshed lab running for later exploration.

## Headlamp cluster viewer

Path: `k8s/headlamp`

The [read-only Headlamp pilot](headlamp/README.md) pins Helm chart 0.45.0, uses a restricted namespace, the built-in `view` role plus a narrowly scoped Node reader, and exposes only a ClusterIP Service for local port-forwarding. Its runbook records the observed four Ready nodes, resource metrics, startup Event, RBAC checks, and reconciliation/rollback commands.

## Validation

From the repository root:

```powershell
python .\scripts\validate-k8s-manifests.py
```

CI also runs `promtool check config` against the Prometheus configuration embedded in its ConfigMap.
