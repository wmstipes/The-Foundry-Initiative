# Milestone 012 — Versioned Release 0.5.0

Date: 2026-08-28

## Result

Released the SignalForge Restaurant API as version `0.5.0`.

## Release tag

v0.5.0

## Docker image

wmstipes/signalforge-restaurant-api:0.5.0

## What changed

- Updated the Restaurant API application version to `0.5.0`
- Updated the GitHub Actions Docker workflow to respond to semantic version tags
- Configured tagged releases like `v0.5.0` to publish Docker image tag `0.5.0`
- Deployed the versioned image to the SignalForge Kubernetes cluster
- Updated the Kubernetes ConfigMap so `/version` reports `0.5.0`

## Confirmed

- GitHub Actions workflow completed successfully
- Docker Hub received the `0.5.0` image tag
- Kubernetes Deployment used image `wmstipes/signalforge-restaurant-api:0.5.0`
- `/version` returned application version `0.5.0`
- The Restaurant API remained healthy after the release deployment

## Lesson learned

A Docker image tag and an application version are related but not the same thing.

The image tag identifies the deployable container artifact.

The application version identifies what the running software reports about itself.

For a clean release, both should be intentionally aligned.

## Why it matters

This milestone created the first proper release loop for the project:

source code
→ version update
→ Git tag
→ GitHub Actions build
→ Docker Hub release image
→ Kubernetes deployment
→ runtime version verification

## Next

Move Kubernetes manifests into version control so the cluster configuration is managed declaratively from the repository.
