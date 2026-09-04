# SignalForge Milestone 004 — FastAPI Deployed from Docker Image

Date: 2026-08-27

## Result

The FastAPI Restaurant API was deployed to the SignalForge Kubernetes cluster using a real Docker image hosted on Docker Hub.

## Image

wmstipes/signalforge-restaurant-api:0.2.0

## Namespace

forge-restaurant

## Workload

- Deployment: restaurant-api
- Replicas: 3
- Service: restaurant-api
- Service Type: ClusterIP
- Runtime: containerd
- Platform: linux/arm64

## Confirmed

- Docker image built successfully for Raspberry Pi arm64 nodes
- Image pushed to Docker Hub
- Kubernetes pulled and ran the image
- ConfigMap-mounted application code was replaced with image-based application code
- /version endpoint returned version 0.2.0
- /menu endpoint returned expected JSON
- Readiness and liveness probes passed

## Learning Translation

Restaurant analogy:
The restaurant is no longer using a handwritten recipe taped to the counter. It now ships as a sealed franchise kitchen package that every location can pull and run.

Kubernetes translation:
The application is now packaged as a versioned container image and deployed through a Kubernetes Deployment using a stable image tag.

## Next

- Add a Kubernetes ConfigMap for environment-specific app settings
- Add rolling update practice with version 0.3.0
- Add a simple /analyze endpoint as the first AI troubleshooting API
