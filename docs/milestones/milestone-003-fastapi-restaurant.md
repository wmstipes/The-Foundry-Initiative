# SignalForge Milestone 003 — FastAPI Restaurant Service Deployed

Date: 2026-08-27

## Result

A FastAPI learning-lab service was deployed successfully to the SignalForge Kubernetes cluster.

## Namespace

forge-restaurant

## Workload

- Deployment: restaurant-api
- Replicas: 3
- Service: restaurant-api
- Service Type: ClusterIP
- App Version: 0.1.0

## Endpoints

- /
- /health
- /ready
- /version
- /menu

## Confirmed

- FastAPI starts successfully inside Kubernetes Pods
- Pods schedule across the worker nodes
- Readiness and liveness probes work
- ClusterIP Service routes traffic to the FastAPI Pods
- In-cluster curl testing returns JSON responses

## Learning Translation

Restaurant analogy:
The restaurant district now has its first real custom restaurant counter running.

Kubernetes translation:
A FastAPI service is running as a replicated Kubernetes Deployment behind a stable ClusterIP Service with health checks and resource controls.

## Next

- Replace ConfigMap-mounted app code with a real container image
- Create Dockerfile
- Build ARM64 image
- Push image to a registry
- Redeploy FastAPI using the versioned image
