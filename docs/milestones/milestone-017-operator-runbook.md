# Milestone 017 — Restaurant API Operator Runbook

Date: 2026-09-04

## Result

Added a complete operator runbook for the SignalForge Restaurant API.

## Runbook

docs/runbooks/restaurant-api-operator-runbook.md

## What the runbook covers

- System overview
- Current application details
- Cluster nodes
- Public lab URLs
- Repository paths
- Normal operating workflow
- Deployment process
- Smoke tests
- Image checks
- Pod checks
- Log review
- Manual Kubernetes checks
- Kubernetes context troubleshooting
- ImagePullBackOff troubleshooting
- ConfigMap restart behavior
- Rollout troubleshooting
- Readiness probe troubleshooting
- NodePort troubleshooting
- Service endpoint troubleshooting
- Rollback procedure
- Roll-forward procedure
- Release procedure
- Recovery checklist
- Restaurant analogy
- Success standard

## Confirmed

- Runbook was created under `docs/runbooks`
- Runbook was rewritten to avoid broken nested markdown code fences
- Runbook documents the current `0.5.0` Restaurant API release
- Runbook explains how to operate the app from the Windows laptop
- Runbook references the helper scripts created in earlier milestones

## Why it matters

This turns the project from a working lab into an operable platform.

A future operator, including future-me, can now understand how to check health, deploy, troubleshoot, roll back, and validate the service without relying only on memory.

## Lesson learned

Working systems need operational documentation.

The runbook is the bridge between “I got it working once” and “I can operate and recover it reliably.”

## Next

Add CI validation for Kubernetes manifests so bad YAML or obvious manifest mistakes are caught before applying changes to the cluster.
