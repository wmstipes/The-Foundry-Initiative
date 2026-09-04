# Milestone 014 — Configure Laptop kubectl Access

Date: 2026-09-04

## Result

Configured Windows laptop kubectl access to the SignalForge Kubernetes cluster.

## What changed

The laptop now has a local kubeconfig that points to the Raspberry Pi Kubernetes control plane.

This allows Kubernetes resources to be viewed, applied, and managed from the laptop instead of only from `forge-head`.

## Confirmed

- kubeconfig was copied from `forge-head`
- Windows `KUBECONFIG` was pointed at the SignalForge kubeconfig
- `kubectl get nodes` worked from Windows
- `kubectl get all -n forge-restaurant` worked from Windows
- `kubectl apply -f k8s/fastapi-restaurant/` worked from Windows
- Windows kubectl no longer falls back to `localhost:8080`

## Why it matters

This completes the local development control loop:

edit files on laptop
→ commit changes to GitHub
→ build images with GitHub Actions
→ apply Kubernetes manifests from laptop
→ update the Raspberry Pi cluster

## Lesson learned

A Kubernetes manifest can be correct, but `kubectl` still needs a valid kubeconfig and cluster context before it can apply anything.

The earlier `localhost:8080` error was not a manifest problem. It was a missing local Kubernetes context problem.

## Security note

The kubeconfig contains cluster credentials and should not be committed to GitHub.

## Next

Create a repeatable deployment helper so applying and validating the Restaurant API becomes a simple, documented command.
