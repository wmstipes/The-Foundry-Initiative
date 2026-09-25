# Istio learning pilot — admission review

**Status at writing:** Source-only assessment; no mesh install or live inventory accepted yet.
**Date:** 2026-09-24

**Subsequent outcome (2026-09-25):** The reviewed minimal Istio control plane
and [isolated persistent learning lab](../../k8s/istio-lab/README.md) are now
running. This page records the earlier admission criteria and should not be
read as the current cluster state. See [project status](../project-status.md)
and the lab runbook for the live state and recovery instructions.

## Question and recommendation

Can a small, reversible service-mesh exercise teach traffic behavior on the
four-node SignalForge Pi cluster without destabilizing the Restaurant API,
Service Pulse, observability, or ForgeOps? Proceed with read-only inventory,
then decide whether an isolated training workload merits installation. Do not
inject the existing application or logging namespaces in the first exercise.
Mesh inspection in ForgeOps Console is a separate product decision.

This is a learning pilot, not a prerequisite for existing ForgeOps incident
evidence. A successful first exercise would show a deliberately chosen client
and service exchanging traffic with and without the mesh, record the resulting
identity/traffic evidence and resource cost, and return to baseline. Avoid
installing Kiali, gateways, tracing, or a Console plugin just to demonstrate
the first concept.

## Known facts and open gates

| Gate | Current evidence | Decision before install |
| --- | --- | --- |
| Kubernetes | Prior cluster baseline says v1.36.4; recheck live. Istio's current supported-release table lists Kubernetes 1.36 for the supported 1.30 and 1.31 lines. | Select and pin an exact maintained patch release; confirm supported K8s version on the day of installation. |
| Architecture | Four Raspberry Pi nodes; Restaurant API is published for ARM64. | Verify every proposed Istio image has a `linux/arm64` manifest and record the exact OCI digests; do not infer this from the application image. |
| Primary CNI | Milestone 001 records Calico installed. | Confirm running Calico version, health, and NetworkPolicy behavior. Review its interaction with the selected Istio data plane. |
| Headroom | No current per-node allocatable, requests, or usage measurement in this assessment. | Measure capacity across all four nodes and projected Istio Pods; define a safe stopping threshold before choosing placement. |
| Existing traffic | Restaurant API and Pulse are live; Loki/Alloy recovery proved, seven-day retention is still pending. | Keep those namespaces out of mesh membership; establish a baseline of their health and resource usage. |
| Permissions | No installation authorized by this assessment. | Review the exact rendered manifest, CRDs, cluster-scoped RBAC, webhook configuration, node access, and rollback with the operator. |

Official references: [supported releases](https://istio.io/latest/docs/releases/supported-releases/), [installation profiles](https://istio.io/latest/docs/setup/additional-setup/config-profiles/), [sidecar and ambient comparison](https://istio.io/latest/docs/overview/dataplane-modes/), [Istio CNI privileges](https://istio.io/latest/docs/setup/additional-setup/cni/), and [ambient prerequisites](https://istio.io/latest/docs/ambient/install/platform-prerequisites/). These pages change; recheck them when choosing a release.

## Choice to evaluate

Start by assessing a **sidecar pilot with the minimal profile**, one new
training namespace, no ingress gateway, and manual injection limited to
training Pods. The minimal profile installs only the control-plane components;
individual mesh workloads add a proxy and, without Istio CNI, a network setup
init container requiring `NET_ADMIN` and `NET_RAW`. Review these permissions
and the Pod security policy before using that route. Istio CNI is optional in
sidecar mode but would put a privileged node agent on every node.

Ambient mode is a valid later comparison, but it requires Istio CNI and
node-level ztunnel components even if only a small training namespace joins.
Its footprint and node-level privileges make it a larger first experiment
on this cluster. This preference is provisional until live headroom and exact
manifest review.

## First read-only inventory

Run from the laptop with the expected context. These commands only read
Kubernetes state; share outputs after reviewing them for local identifiers.

```powershell
kubectl config current-context
kubectl version
kubectl get nodes -o wide
kubectl top nodes
kubectl describe nodes
kubectl -n kube-system get daemonsets,pods -o wide
kubectl get namespaces --show-labels
kubectl get crd | Select-String 'istio|gateway.networking.k8s.io'
kubectl get mutatingwebhookconfigurations,validatingwebhookconfigurations | Select-String 'istio'
kubectl get pods -A -o wide
```

For each node, compare `Allocatable` and `Allocated resources` in the
`describe` output with actual `top` samples; neither alone establishes
reliable spare capacity. Confirm the existing application/Pulse/Loki health
and the Calico DaemonSet before deciding on an install profile. Stop if node
pressure, degraded CNI, unexpected Istio objects, or insufficient space is
found. Do not use `kubectl apply`, `istioctl install`, namespace injection
labels, or Pod restarts in this gate.

## Proposed later exercise and exit criteria

Only after exact image/platform, resource, privilege, network, baseline and
rollback review, stage a separate installation decision. The smallest useful
exercise is two disposable training workloads: record unmeshed request
success, enroll only those workloads, show observed proxy identity/traffic
data, compare steady-state CPU/memory and request behavior, then remove the
training resources and Istio components using the reviewed inventory. Require
unaffected existing services throughout. Keep the training manifests and
uninstall sequence version controlled before any cluster change. A failed
gate means defer the mesh, with the measured reason recorded here.
