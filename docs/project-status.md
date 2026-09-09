# Project Status

**Last updated:** 2026-09-08

**Current phase:** Operational visibility and durable monitoring

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API, a lightweight Prometheus collection layer, and Kubernetes Metrics Server.

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

## Current observability state

- Prometheus namespace: `forge-observability`
- One Prometheus replica
- Image: `prom/prometheus:v3.13.2`
- Pod discovery restricted to `forge-restaurant`
- RBAC restricted to get, list, and watch Pods
- Scrape interval: 30 seconds
- Retention: 48 hours, capped at 750 MB
- Storage: 1 GiB ephemeral `emptyDir`
- Access: ClusterIP plus `kubectl port-forward`
- Healthy Restaurant API targets: 3
- Prometheus Pod: stable with zero restarts after rollout
- Automatic target rediscovery: confirmed through application Pod replacement
- Request-duration histogram: available across all three application Pods
- Traffic classification: `application` and `synthetic`
- Cardinality protection: unmatched URLs use `path="unmatched"`
- Baseline queries: `docs/observability/prometheus-queries.md`

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

## Immediate next step

Plan Milestone 025 around persistent NVMe-backed Prometheus storage. Define storage placement, failure behavior, retention, backup expectations, and recovery steps before changing the live collector.

## Known temporary limitation

Prometheus history is intentionally ephemeral. Replacing or rescheduling its Pod removes collected history until NVMe-backed persistent storage is designed and introduced.

Kubelet serving-certificate rotation can create new pending CSRs. Core Kubernetes does not automatically approve these serving requests, so an operator must validate the requester, signer, usages, subject, and SAN ownership before approval.
