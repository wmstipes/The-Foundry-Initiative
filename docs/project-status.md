# Project Status

**Last updated:** 2026-09-08

**Current phase:** Engineering maturity and observability

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API and a lightweight Prometheus collection layer.

The project has moved from basic workload deployment into repeatable engineering operations: automated tests, GitHub Actions, ARM64 image publishing, version-controlled Kubernetes manifests, validation, helper commands, a runbook, and application metrics.

## Current application

- Application: SignalForge Restaurant API
- Namespace: `forge-restaurant`
- Deployment: `restaurant-api`
- Replicas: 3
- Release: `0.6.0`
- Image: `wmstipes/signalforge-restaurant-api:0.6.0`
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

## In progress

Milestone 023 — Application Metrics Refinement

Implementation is prepared for Restaurant API `0.7.0`. It adds an aggregatable request-duration histogram, separates application and synthetic traffic through a bounded label, and normalizes unmatched paths to protect metric cardinality.

The immediate next step is to run the full developer preflight, commit and push the change, publish the `0.7.0` release image, deploy it, and verify the baseline PromQL queries against all three replicas.

## Known temporary limitation

Prometheus history is intentionally ephemeral. Replacing or rescheduling its Pod removes collected history until NVMe-backed persistent storage is designed and introduced.

The Kubernetes Metrics API is not installed, so `kubectl top` is not currently available. This is separate from Prometheus application-metrics collection.
