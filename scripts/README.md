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
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-targets
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-ui
```

`metrics-ui` keeps running while the port-forward is open. Press Ctrl+C to stop it.

## Direct helpers

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-restaurant-api.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-prometheus.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\test-prometheus-targets.ps1
```

## Manifest validation

```powershell
python .\scripts\validate-k8s-manifests.py
```
