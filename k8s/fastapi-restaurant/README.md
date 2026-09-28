# SignalForge Restaurant API Kubernetes Manifests

These manifests define the Kubernetes resources for the SignalForge Restaurant API.

## Resources

- `namespace.yaml` — creates the `forge-restaurant` namespace
- `restaurant-api-config.yaml` — runtime configuration using a ConfigMap
- `restaurant-api-deployment.yaml` — FastAPI application Deployment
- `restaurant-api-service.yaml` — internal ClusterIP Service
- `restaurant-api-nodeport.yaml` — external lab access through NodePort `30080`

## Current version

Application version: `0.7.0`

Docker image:

```text
wmstipes/signalforge-restaurant-api:0.7.0
```

## Metrics

Each Restaurant API Pod exposes Prometheus-format metrics at `/metrics` on its named `http` container port. The lightweight collector under `k8s/prometheus` discovers and scrapes the Pods individually.

## Private HTTPS access

The portal also links to the Restaurant API through the private HTTPS gateway.
NodePort remains a separate lab HTTP path; TLS terminates at the gateway.
See the [gateway runbook](../lan-portal/README.md).
