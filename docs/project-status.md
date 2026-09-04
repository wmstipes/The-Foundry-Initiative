# Project Status

**Last updated:** 2026-09-04

**Current phase:** Engineering maturity and observability

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API and now has a ready-to-deploy lightweight Prometheus collection layer.

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

## In progress

Milestone 022 - Lightweight Prometheus Metrics Collection

Implementation is present in the repository. Local structural validation passes. Cluster rollout, live target verification, and GitHub Actions `promtool` verification remain to be completed.

## Milestone 022 design

- Namespace: `forge-observability`
- One Prometheus replica
- Image: `prom/prometheus:v3.13.2`
- Pod discovery restricted to `forge-restaurant`
- RBAC restricted to get, list, and watch Pods
- Scrape interval: 30 seconds
- Retention: 48 hours, capped at 750 MB
- Storage: 1 GiB ephemeral `emptyDir`
- Access: ClusterIP plus `kubectl port-forward`

## Immediate next step

Deploy Prometheus from the Windows laptop:

```powershell
.\scripts\forge.ps1 metrics-deploy
```

The deployment helper will apply the manifests, verify Pod-discovery permission, wait for the rollout, and require three healthy Restaurant API targets.

## Known temporary limitation

Prometheus history is intentionally ephemeral. Replacing or rescheduling its Pod removes collected history until NVMe-backed persistent storage is designed and introduced.
