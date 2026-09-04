# Milestone 022 - Lightweight Prometheus Metrics Collection

Date: 2026-09-04

Status: Implementation ready; cluster validation pending

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
- [ ] `promtool check config` passes in GitHub Actions.
- [ ] Prometheus starts successfully on ARM64.
- [ ] Prometheus can list Pods in `forge-restaurant`.
- [ ] The target check reports three healthy Restaurant API targets.
- [ ] Custom `restaurant_api_` metrics are queryable over time.
- [ ] Replacing one Restaurant API Pod removes the old target and discovers the replacement.
- [ ] The UI is reachable only through `kubectl port-forward`.
- [ ] Resource use remains within the configured limits.
- [ ] Ephemeral-history behavior is documented and understood.

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

## Next validation step

Deploy from the Windows laptop, confirm three healthy targets, and exercise automatic target rediscovery by replacing one Restaurant API Pod.
