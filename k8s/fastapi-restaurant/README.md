# SignalForge Restaurant API Kubernetes Manifests

These manifests define the Kubernetes resources for the SignalForge Restaurant API.

## Resources

- `namespace.yaml` — creates the `forge-restaurant` namespace
- `restaurant-api-config.yaml` — runtime configuration using a ConfigMap
- `restaurant-api-deployment.yaml` — FastAPI application Deployment
- `restaurant-api-service.yaml` — internal ClusterIP Service
- `restaurant-api-nodeport.yaml` — external lab access through NodePort `30080`

## Current version

Application version: `0.5.0`

Docker image:

```text
wmstipes/signalforge-restaurant-api:0.5.0
