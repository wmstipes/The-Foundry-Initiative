# Milestone 011 — Automated Docker Image Build

Date: 2026-08-28

## Result

Added a GitHub Actions workflow that tests, builds, and pushes the SignalForge Restaurant API Docker image automatically.

## Workflow

Restaurant API Docker Build

## Application path

apps/restaurant-api

## Docker image

wmstipes/signalforge-restaurant-api

## What the workflow does

- Runs on pushes to main when Restaurant API files change
- Supports manual workflow dispatch
- Runs the Restaurant API test suite first
- Sets up Docker QEMU support
- Sets up Docker Buildx
- Logs in to Docker Hub using GitHub repository secrets
- Builds a linux/arm64 image for Raspberry Pi nodes
- Pushes the image to Docker Hub

## Tags produced

- latest
- commit SHA tag

## Confirmed

- Initial Docker login failed because the secret name/token setup was incorrect
- GitHub repository secrets were corrected
- Workflow rerun completed successfully
- Test job passed
- Build and push job passed
- Docker Hub authentication worked
- ARM64 image build completed successfully

## Lesson learned

CI/CD workflows depend on both code and environment configuration. The workflow logic can be correct, but a missing or misnamed secret will still break the delivery pipeline.

## Why it matters

The laptop is no longer the only build machine. The project now has a repeatable CI/CD path:

code change
→ GitHub Actions tests
→ Docker image build
→ Docker Hub push
→ Kubernetes deployment target

## Next

Deploy the GitHub-built image to the SignalForge Kubernetes cluster using the commit SHA tag.
