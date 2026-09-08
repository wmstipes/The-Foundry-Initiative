# Milestone 022 - Lightweight Prometheus Metrics Collection

Started: 2026-09-04

Completed: 2026-09-08

Status: Complete

## Goal

Collect and retain Restaurant API metrics from all three application Pods with a small, bounded Prometheus deployment.

## Implementation

- Added the `forge-observability` namespace.
- Added a dedicated Prometheus ServiceAccount.
- Added a Role and RoleBinding limited to Pod discovery in `forge-restaurant`.
- Added a Prometheus scrape job that selects Restaurant API containers on the named `http` port and retains Pod phase and readiness as target labels.
- Pinned Prometheus to the `prom/prometheus:v3.13.2` LTS patch release, which provides an ARM64 image.
- Limited Prometheus to one replica, a 30-second scrape interval, 48-hour retention, and 750 MB of retained blocks.
- Added a 1 GiB `emptyDir` volume.
- Set CPU and memory requests and limits.
- Exposed Prometheus only through a ClusterIP Service.
- Added deployment, target-check, status, and port-forward helper commands.
- Extended manifest validation and added `promtool check config` to CI.

## Resource guardrails

```yaml
requests:
  cpu: 100m
  memory: 256Mi
limits:
  cpu: 500m
  memory: 512Mi
```

## Acceptance criteria

- [x] Kubernetes manifest validation passes locally.
- [x] `promtool check config` passes in GitHub Actions.
- [x] Prometheus starts successfully on ARM64.
- [x] Prometheus can list Pods in `forge-restaurant`.
- [x] The target check reports three healthy Restaurant API targets.
- [x] Custom `restaurant_api_` metrics are queryable over time.
- [x] Replacing one Restaurant API Pod removes the old target and discovers the replacement.
- [x] The UI is reachable only through `kubectl port-forward`.
- [x] Resource requests and limits are applied, and the Prometheus Pod remains stable with zero restarts.
- [x] Ephemeral-history behavior is documented and understood.

## Confirmed on SignalForge

- Prometheus Pod: `1/1 Running`
- Prometheus image: `prom/prometheus:v3.13.2`
- Scheduled node: `forge-node-03`
- Unexpected restarts: `0`
- Healthy Restaurant API targets: `3`
- Prometheus UI reachable at `http://localhost:9090` through `kubectl port-forward`
- `restaurant_api_requests_total` returns time-series data grouped by path and status
- Readiness and liveness request counts reflect their configured 10-second and 20-second probe intervals
- Pod replacement test removed the old target and discovered the replacement automatically

## Operator commands

```powershell
.\scripts\forge.ps1 metrics-deploy
.\scripts\forge.ps1 metrics-status
.\scripts\forge.ps1 metrics-targets
.\scripts\forge.ps1 metrics-ui
```

## Expected query result

```promql
count(up{job="restaurant-api"} == 1)
```

Expected value: `3`

## Data-loss behavior

Prometheus history is intentionally ephemeral during this milestone. Replacing or rescheduling the Prometheus Pod deletes the stored time series. Persistent NVMe-backed storage is a later milestone.

## Metrics API note

`kubectl top` reports `Metrics API not available` because Kubernetes Metrics Server is not installed. Prometheus does not provide the `metrics.k8s.io` API used by `kubectl top`. This does not affect Prometheus scraping or querying.

Live Kubernetes resource-usage reporting remains a possible future milestone. For this milestone, the configured resource guardrails and the stable zero-restart Pod satisfy the operational acceptance check.

## Implementation correction

The first target-check helper passed a multiline `sh -c` program through Windows PowerShell and `kubectl`. Windows argument handling produced an unterminated shell string inside the temporary curl Pod.

The helper was corrected to:

- Start one temporary curl Pod with a simple `sleep` command
- Poll Prometheus from PowerShell using `kubectl exec`
- Parse the Prometheus JSON response in PowerShell
- Delete the temporary Pod in a `finally` block

The corrected helper successfully reported three healthy targets.

## Lesson learned

Cross-platform automation should avoid passing complex multiline shell programs through Windows PowerShell into Linux containers. Keeping control flow in PowerShell and sending simple commands through `kubectl exec` is easier to reason about and more reliable.

## Next

Choose the next small observability milestone. Candidates include baseline PromQL queries, application latency metrics, Kubernetes Metrics Server, persistent NVMe-backed storage, or a first Grafana dashboard.
