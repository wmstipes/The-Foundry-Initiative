# Milestone 013 — Kubernetes Manifests Under Version Control

Date: 2026-09-04

## Result

Moved the SignalForge Restaurant API Kubernetes manifests into The Foundry Initiative repository.

## Manifest path

k8s/fastapi-restaurant

## Resources managed declaratively

- Namespace
- ConfigMap
- Deployment
- ClusterIP Service
- NodePort Service
- Kubernetes README

## Confirmed

- Manifests were committed to the repository
- Repository was pulled onto forge-head
- Manifests applied successfully from forge-head
- Kubernetes accepted the declared state
- Restaurant API remained healthy after applying the repo-managed manifests
- Application version remained aligned with the expected release

## Lesson learned

The Kubernetes cluster should not depend only on commands typed by hand. Storing manifests in Git creates a repeatable source of truth for rebuilding, reviewing, and improving the environment.

## Why it matters

This is the first real GitOps-style step in the project:

application code
→ CI tests
→ Docker image
→ Kubernetes manifests
→ cluster declared state

## Important note

Laptop kubectl is not configured yet. The laptop has the manifests, but forge-head currently has the working kubeconfig for the cluster.

## Next

Configure laptop kubectl access to the SignalForge cluster so manifests can be applied from the laptop as well as from forge-head.
