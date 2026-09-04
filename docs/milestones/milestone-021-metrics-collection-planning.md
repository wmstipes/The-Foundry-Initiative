# Milestone 021 - Metrics Collection Planning

Date: 2026-09-04

## Result

Selected a single, lightweight Prometheus server as SignalForge's first metrics collector.

## Options considered

- One-off scraping with curl
- Prometheus running outside the cluster
- A single in-cluster Prometheus server
- `kube-prometheus-stack`

## Decision

Deploy one Prometheus Pod inside SignalForge using plain Kubernetes manifests.

The first deployment will include:

- Namespace-scoped Kubernetes Pod discovery
- One Prometheus replica
- 30-second scraping
- 48-hour retention
- A 750 MB retention-size cap
- A 1 GiB ephemeral volume
- ClusterIP-only access through `kubectl port-forward`
- Explicit CPU and memory guardrails

## Deferred

- Grafana
- Alertmanager
- node-exporter
- kube-state-metrics
- Prometheus Operator and ServiceMonitor resources
- Persistent storage
- Remote write
- `kube-prometheus-stack`

## Why this design

The Restaurant API currently has three replicas and is the only application that needs time-series collection. Direct Pod discovery lets Prometheus scrape all three replicas individually without introducing the operational weight of a full monitoring platform.

The permissions are intentionally namespace-scoped. Prometheus only needs to get, list, and watch Pods in `forge-restaurant` for this milestone.

## Storage decision

The first collector uses ephemeral storage to avoid committing the lab to an SD-card-backed persistent-volume design. Metrics history will be lost if the Prometheus Pod is replaced. That tradeoff is accepted until the NVMe-backed storage design is ready.

## Next

Deploy and verify the lightweight Prometheus collector as Milestone 022.
