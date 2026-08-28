# Milestone 010 — Restaurant API CI

Date: 2026-08-28

## Result

Added a GitHub Actions CI workflow for the SignalForge Restaurant API.

## Workflow

Restaurant API CI

## Application path

apps/restaurant-api

## What the workflow does

- Runs on pushes to main when Restaurant API files change
- Runs on pull requests that touch Restaurant API files
- Supports manual workflow dispatch
- Checks out the repository
- Sets up Python 3.12
- Installs application and development dependencies
- Runs pytest

## Confirmed

- Workflow appeared in the GitHub Actions tab
- First workflow run completed successfully
- GitHub Actions returned a green check
- Restaurant API tests passed in CI

## Lesson learned

The project now has an automated quality gate. Instead of only testing locally on the laptop, GitHub verifies the Restaurant API in a clean CI environment.

## Why it matters

This turns the project from a local lab exercise into a more professional engineering workflow:

local code change
→ commit
→ push
→ automated test validation
→ visible evidence of working software

## Next

Add Docker image build automation so successful changes can produce a linux/arm64 image for the Raspberry Pi Kubernetes cluster.
