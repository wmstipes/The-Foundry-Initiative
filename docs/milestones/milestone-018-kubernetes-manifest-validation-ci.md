# Milestone 018 — Kubernetes Manifest Validation in CI

Date: 2026-09-04

## Result

Added GitHub Actions validation for the SignalForge Kubernetes manifests.

## Workflow

Kubernetes Manifest Validation

## Validation script

scripts/validate-k8s-manifests.py

## What the validation checks

- Required Kubernetes manifest files exist
- YAML files parse correctly
- Namespace is `forge-restaurant`
- ConfigMap uses the expected application version
- ConfigMap has `FEATURE_ANALYZE_ENABLED` enabled
- Deployment name is `restaurant-api`
- Deployment namespace is correct
- Pod labels match the application selector
- Container image uses the expected Docker image repository
- Readiness probe exists
- Liveness probe exists
- Resource requests and limits exist
- Internal Service is `ClusterIP`
- Internal Service selector matches the app label
- NodePort Service is `NodePort`
- NodePort Service selector matches the app label
- NodePort is `30080`

## Confirmed

- Validation script was added to the repository
- GitHub Actions workflow was added
- Workflow runs on Kubernetes manifest changes
- Workflow can be run manually
- All GitHub Actions checks are green
- Kubernetes manifests are now checked before being trusted for deployment

## Why it matters

The project now validates both application code and Kubernetes configuration.

Before this milestone, a bad Kubernetes manifest could be committed and only discovered during `kubectl apply`.

Now obvious manifest mistakes can be caught earlier in CI.

## Lesson learned

CI should not only test application code.

For platform engineering, CI should also validate the infrastructure and deployment definitions that run the application.

## Current CI/CD coverage

The repository now has checks for:

- Restaurant API Python tests
- Docker image build and push
- Versioned Docker release tags
- Kubernetes manifest validation

## Jenkins note

A Jenkins server is not required at this stage.

GitHub Actions already provides the CI/CD capability needed for this lab. Jenkins may be useful later as a separate enterprise CI/CD comparison exercise, but adding it now would increase operational overhead before the core platform needs it.

## Next

Add a task runner or Makefile-style command layer so common local operations are easier to discover and run.
