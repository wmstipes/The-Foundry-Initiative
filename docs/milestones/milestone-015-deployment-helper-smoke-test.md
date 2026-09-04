# Milestone 015 — Deployment Helper and Smoke Test

Date: 2026-09-04

## Result

Added a deployment helper script for the SignalForge Restaurant API.

## Script

scripts/deploy-restaurant-api.ps1

## What the helper does

- Uses the current Kubernetes context from the laptop
- Applies the Kubernetes manifests from the repository
- Waits for the Restaurant API Deployment rollout to complete
- Lists the current Restaurant API Pods
- Shows the currently deployed container image
- Runs an in-cluster smoke test against `/version`
- Runs an in-cluster smoke test against `/status`
- Deletes temporary curl test Pods after each smoke test

## Confirmed

- The helper ran from the Windows laptop
- Laptop kubectl communicated with the SignalForge cluster
- Manifests applied successfully
- Rollout completed successfully
- Restaurant API Pods were healthy
- `/version` returned successfully
- `/status` returned successfully

## Why it matters

This creates a repeatable deployment workflow.

Instead of remembering several individual kubectl commands, the project now has a single repo-managed command that deploys and validates the application.

## Lesson learned

A deployment is not finished when manifests are applied.

A complete deployment should also verify rollout status, running Pods, deployed image, and application health.

## Next

Add a Makefile or task runner so common development actions become simple commands.
