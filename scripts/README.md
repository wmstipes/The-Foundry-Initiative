# Scripts

This folder contains helper scripts for operating and developing The Foundry Initiative.

## Developer helper

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 status
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 test
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 validate-k8s
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 deploy
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 smoke
powershell -ExecutionPolicy Bypass -File .\scripts\foundry.ps1 preflight
```

## SignalForge operator helper

Restaurant API commands:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 deploy
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 pods
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 logs
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 image
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 nodes
```

Prometheus commands:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-deploy
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-storage
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-persistence
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-backup-ready
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-backup
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-restore-test
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-targets
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-ui
```

`metrics-storage` checks the static StorageClass, PV, PVC, node placement, retention, and ClusterIP-only access. `metrics-persistence` deliberately replaces the Prometheus Pod and proves that a known historical sample survives.

`metrics-backup-ready` reads Prometheus's own loaded-block gauge and succeeds only after at least one compacted block exists. `metrics-backup` runs that same gate before downtime, briefly scales Prometheus to zero, and streams a cold archive directly to `%USERPROFILE%\SignalForge-Backups\prometheus`; it retains the four newest archives and always attempts to restore the collector to one replica. `metrics-restore-test` verifies the newest archive's checksum, restores it into an isolated NVMe directory, runs `promtool` against that copy, and removes only the temporary restored copy. It may prompt for the `forge-head` sudo password when creating and removing the isolated directory.

`metrics-ui` keeps running while the port-forward is open; press Ctrl+C to stop it.

Kubernetes resource-metrics commands:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-server-deploy
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-server-status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 top
```

`metrics-server-status` checks the deployment, secure kubelet-CA argument, aggregated API availability, node-metric coverage, recent scrape errors, and current usage. `top` shows current node, Restaurant API, Prometheus, and Metrics Server CPU and memory usage.

## Direct helpers

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-restaurant-api.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-prometheus.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\backup-prometheus.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-backup-ready.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-storage.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-persistence.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-restore.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-targets.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-metrics-server.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-metrics-server.ps1
```

## Manifest validation

```powershell
python .\scripts\validate-k8s-manifests.py
```

## Limited alert validation and guarded activation (Milestone 030)

```powershell
python .\scripts\validate-alert-rules.py
python -m unittest discover -s tests -p 'test_alert_rules.py'
```

These are source-level checks only. For actual rule evaluation with an existing promtool 3.13.2 binary, use `python .\scripts\test-alert-rules.py --promtool "C:\path\to\promtool.exe"` or the alert-rule CI job. Missing/wrong-version tooling fails rather than reporting a skipped success.

The guarded operator helper defaults to a non-mutating plan:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-alerts-plan
```

It checks the exact live ConfigMap state, context, image, replica and target baseline; reports 24 hours of scoped coverage history; performs server-side validation and `kubectl diff`; and exits without changing cluster objects. There is deliberately no generic `forge.ps1` activation command. After separate approval, use the direct helper with `-Activate`; it snapshots the baseline ConfigMap, rolls out only Prometheus, verifies both rules are healthy and inactive, and automatically rolls back on failure. See the [activation review](../docs/observability/limited-alerting-activation-review.md) for commands, constraints and recovery.
