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

## Validation

From the repository root:

```powershell
python .\scripts\validate-k8s-manifests.py
```

CI also runs `promtool check config` against the Prometheus configuration embedded in its ConfigMap.
