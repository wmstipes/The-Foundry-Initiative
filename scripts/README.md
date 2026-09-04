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
Operator helper
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 deploy
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 pods
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 logs
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 image
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 nodes
Deployment helper
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-restaurant-api.ps1
Validation helper
python .\scripts\validate-k8s-manifests.py

