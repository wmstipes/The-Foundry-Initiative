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

## Service Pulse candidate

Path: `k8s/service-pulse`

This directory contains a proposed restricted `forge-pulse` namespace, one probe and one board Deployment, and their internal ClusterIP Services. Both pin the published `0.1.1` OCI digest. The board is accessible by port-forward only from outside the cluster. See its README for read-only preflight, phased review, acceptance, and scoped rollback. These resources have not been applied to the cluster.

## Validation

From the repository root:

```powershell
python .\scripts\validate-k8s-manifests.py
```

CI also runs `promtool check config` against the Prometheus configuration embedded in its ConfigMap.
