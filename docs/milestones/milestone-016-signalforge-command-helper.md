# Milestone 016 — SignalForge Command Helper

Date: 2026-09-04

## Result

Added a SignalForge command helper script for common Kubernetes operations.

## Script

scripts/forge.ps1

## Commands supported

- status
- deploy
- smoke
- pods
- logs
- image
- nodes

## Confirmed

- Helper runs from the Windows laptop
- `status` shows the current Kubernetes context, cluster nodes, and Restaurant API resources
- `deploy` calls the Restaurant API deployment helper
- `smoke` verifies `/version` and `/status`
- `image` shows the currently deployed container image
- `pods` shows the running Restaurant API Pods
- `logs` retrieves recent Restaurant API logs
- Commands use the laptop kubeconfig to communicate directly with the SignalForge cluster

## Why it matters

This turns repeated kubectl commands into a simple operator interface.

Instead of remembering multiple commands, the project now has one script that can check, deploy, test, and inspect the application.

## Lesson learned

Good platform engineering is not only about making things work.

It is also about making the correct operational actions easy to repeat.

## Next

Create an operator runbook that documents how to use the helper, validate deployments, troubleshoot common failures, and recover from problems.
