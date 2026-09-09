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
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-targets
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-ui
```

`metrics-storage` checks the static StorageClass, PV, PVC, node placement, retention, and ClusterIP-only access. `metrics-persistence` deliberately replaces the Prometheus Pod and proves that a known historical sample survives. `metrics-ui` keeps running while the port-forward is open; press Ctrl+C to stop it.

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
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-storage.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-persistence.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-targets.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-metrics-server.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-metrics-server.ps1
```

## Manifest validation

```powershell
python .\scripts\validate-k8s-manifests.py
```
