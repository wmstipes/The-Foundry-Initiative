# Istio 1.31.1 minimal profile: offline manifest review

**Date:** 2026-09-24
**Decision:** No cluster installation yet. The proposed sidecar training pilot needs explicit review of cluster-wide permissions, admission scope, and a disposable privileged training namespace.

## Reproduction

The upstream `istioctl-1.31.1-linux-amd64.tar.gz` release asset was verified against the release SHA-256 `a44563904f22f2a8bf6ac4fff1b0bad9f718587c2be6aa807b83fe9049910639`. No kubeconfig or cluster was used. Commands:

```sh
istioctl manifest generate --set profile=minimal --output istio-minimal-1.31.1.yaml
istioctl manifest generate --set profile=minimal --set values.pilot.autoscaleEnabled=false --output istio-minimal-fixed-1.31.1.yaml
```

The stock manifest is 1,091,272 bytes, SHA-256 `392a794b9413ab481fb4bd40601220d68a5c7b0fcbe2df0a2c2c15d9e28ef4d1`. The fixed-replica variant is 1,090,608 bytes, SHA-256 `040c5542afa78fefdc24473d69284e97bcdd7ecc0887adb82044591b85a7f717`. Hashes identify these offline renderings, not an accepted installation package. The two output manifests are temporary review artifacts, not deployment instructions.

## What the stock profile would add

| Surface | Rendered result | Pilot implication |
| --- | --- | --- |
| API extension | 15 Istio `CustomResourceDefinition` objects | Cluster-wide API surface; removing CRDs later can delete any Istio custom resources. |
| Admission | One mutating webhook configuration with four Pod injection entries and one validating configuration | Cluster-wide objects. Pod injection selectors opt namespaces or Pods in; injection entries use `failurePolicy: Fail`. Review selector behavior and outage response before install. |
| RBAC | Three `ClusterRole` and three `ClusterRoleBinding` objects, plus one namespaced Role/RoleBinding | `istiod` can read Secrets across namespaces, update admission configurations, and has a gateway-controller binding with cluster-wide create/update/delete of Deployments, Services, ServiceAccounts, HPAs, and PodDisruptionBudgets. These permissions are substantially broader than the training namespace. |
| Runtime | One `istiod` Deployment in `istio-system`, one Service, two ServiceAccounts, three ConfigMaps | The control plane is a persistent dependency while training Pods run. The rendered YAML does not create the `istio-system` Namespace. |
| Capacity | `istiod` requests 500m CPU and 2,048 MiB; HPA min 1, max 5 | Resource planning must consider five replicas, not only the initial Pod. One current usage sample is insufficient to promise headroom. |
| Sidecar defaults | Injector values request 100m CPU and 128 MiB memory per proxy, with limits of 2 CPU and 1,024 MiB | Two training Pods add at least 200m CPU and 256 MiB of proxy requests; actual use must be measured. |
| Images | Deployment references `docker.io/istio/pilot:1.31.1`; sidecar injection template references proxy image | The operator separately observed `linux/arm64` manifests for `pilot` and `proxyv2`. The rendered install uses a mutable tag; reconcile image identity and pinning policy before installation. |
| Scope | No Istio CNI DaemonSet, ztunnel, or gateway Deployment in the minimal profile | A sidecar training Pod still requires the Istio init container's `NET_ADMIN` and `NET_RAW` capabilities without Istio CNI. Do not enroll existing workload namespaces. |

The fixed-replica variant removes the HPA and renders `replicas: 1`, but leaves the other surfaces and the 2 GiB request. A further offline render with `values.pilot.env.PILOT_ENABLE_GATEWAY_API=false` puts that environment variable into the Deployment **without removing** the gateway-controller ClusterRole or binding. Do not claim that this setting alone narrows RBAC.

## Recommended first exercise, if admitted later

Use a separate short-lived training namespace with an explicit Pod Security decision; Istio's non-CNI sidecar init container needs capabilities that the `baseline` admission level disallows. Supply two small disposable workloads, with one unmeshed baseline and one explicitly selected meshed case. Do not label `forge-pulse`, `forge-restaurant`, `forge-observability`, or `forge-tools` for injection. Define a resource and time budget and observe application baseline, proxy readiness, request success, and resource use. Avoid gateways, tracing addons, and production routing changes.

Before requesting live install approval, review the full rendered manifest and the intended namespace objects; pin or accept exact image index identities; decide whether the broad default RBAC is acceptable for a training exercise; verify no existing Istio control plane; server dry-run/diff resources where their namespaces and APIs already exist, then validate dependent namespaced resources after the corresponding approved namespace creation. Document expected webhook selectors and a stop procedure. One `istiod` replica makes injection unavailable while it is down; avoid starting or replacing training Pods during that outage. Any actual install and cleanup must be separately reviewed.

For removal, delete training workloads and opt-in labels first, then uninstall the exact Istio installation after verifying no other control plane depends on its shared resources. Upstream documents `istioctl uninstall --purge` for complete removal but warns that it deletes cluster-scoped resources potentially shared by other control planes. Inspect remaining webhooks, roles, CRDs, Pods, and namespaces after removal. This is a procedure to review, not authorization to execute it.

Official references: [Istio 1.31.1 release](https://github.com/istio/istio/releases/tag/1.31.1), [minimal profile](https://istio.io/latest/docs/setup/additional-setup/config-profiles/), [manifest generation](https://istio.io/latest/docs/reference/commands/istioctl/), [sidecar privileges and Istio CNI](https://istio.io/latest/docs/setup/additional-setup/cni/), [Pod Security Admission](https://istio.io/latest/docs/setup/additional-setup/pod-security-admission/), [uninstall guidance](https://istio.io/latest/docs/setup/install/istioctl/).
