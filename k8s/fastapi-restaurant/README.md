# SignalForge Restaurant API Kubernetes Manifests

These manifests define the Kubernetes resources for the SignalForge Restaurant API.

## Resources

- `namespace.yaml` â€” creates the `forge-restaurant` namespace
- `restaurant-api-config.yaml` â€” runtime configuration using a ConfigMap
- `restaurant-api-deployment.yaml` â€” FastAPI application Deployment
- `restaurant-api-service.yaml` â€” internal ClusterIP Service
- `restaurant-api-nodeport.yaml` â€” external lab access through NodePort `30080`

## Current version

Application version: `0.6.0`

Docker image:

```text
wmstipes/signalforge-restaurant-api:0.6.0

