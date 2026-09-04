# Milestone 019 — Developer Command Layer

Date: 2026-09-04

## Result

Added a developer command helper for The Foundry Initiative.

## Script

scripts/foundry.ps1

## Supporting documentation

scripts/README.md

## Commands supported

- status
- test
- validate-k8s
- deploy
- smoke
- preflight

## Confirmed

- Developer helper runs from the Windows laptop
- `status` shows Git state, Kubernetes context, nodes, and Restaurant API resources
- `test` runs the Restaurant API test suite
- `validate-k8s` runs Kubernetes manifest validation
- `deploy` calls the Restaurant API deployment helper
- `smoke` runs application smoke tests
- `preflight` runs the main local checks before pushing changes

## Why it matters

This creates a simple developer workflow for the project.

Instead of remembering separate Git, Python, Kubernetes, and smoke-test commands, common actions are now available through one script.

## Lesson learned

A strong engineering project should make the correct workflow easy to repeat.

The developer command layer turns the lab into something closer to a maintainable platform project.

## Current workflow

Developer changes can now follow this pattern:

edit code or manifests
→ run preflight
→ commit
→ push
→ GitHub Actions validate
→ deploy
→ smoke test

## Next

Add basic application observability so the cluster can show useful runtime information beyond simple health checks.
