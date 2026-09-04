# SignalForge Lightweight Prometheus

These manifests deploy a single Prometheus server for the Restaurant API.

## Scope

- Namespace: `forge-observability`
- Prometheus image: `prom/prometheus:v3.13.2`
- One Prometheus replica
- Pod discovery limited to `forge-restaurant`
- Scrape target limited to Restaurant API containers on the named `http` port
- Scrape interval: 30 seconds
- Retention time: 48 hours
- Retention size: 750 MB
- Storage: 1 GiB `emptyDir`
- Access: `kubectl port-forward` only

No Grafana, Alertmanager, node-exporter, kube-state-metrics, operator, or persistent storage is installed in this milestone.

## Resources

- `namespace.yaml` creates `forge-observability`.
- `prometheus-service-account.yaml` provides the Prometheus workload identity.
- `restaurant-pod-reader-role.yaml` grants read-only Pod discovery in `forge-restaurant`.
- `restaurant-pod-reader-role-binding.yaml` binds that Role to the Prometheus ServiceAccount.
- `prometheus-config.yaml` defines the Restaurant API scrape job.
- `prometheus-deployment.yaml` runs Prometheus with bounded resources and retention.
- `prometheus-service.yaml` provides an internal-only ClusterIP.

## Deploy

From the repository root on the laptop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-deploy
```

## Check collection

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-targets
```

The target query should return `3` while all three Restaurant API Pods are ready.

## Open the Prometheus UI

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-ui
```

Then open `http://localhost:9090`.

## Expected data-loss behavior

Metrics history is intentionally ephemeral. Replacing or rescheduling the Prometheus Pod deletes its stored history. Persistent storage is deferred until SignalForge has an agreed NVMe-backed storage design.
