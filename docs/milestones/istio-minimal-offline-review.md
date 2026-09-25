# Istio 1.31.1 minimal profile: offline review and control-plane checkpoint

**Date:** 2026-09-24
**Status at writing:** The separately approved minimal control plane is installed. The training namespace, workloads, sidecar injection, and Pod Security exception have not been applied.

**Subsequent outcome (2026-09-25):** The [persistent learning lab](../../k8s/istio-lab/README.md)
uses a separate namespace with three injected workloads and a scoped Pod
Security exception. The checkpoint below remains historical evidence, not a
description of the present lab state.

## Control-plane checkpoint

The Windows `istioctl` 1.31.1 archive matched upstream SHA-256 `e77f2c192b54aab2ed480745bedc081b3cedecf177e357a4ea9e739634818f9f`. The locally rendered fixed-replica manifest matched the reviewed SHA-256 `040c5542afa78fefdc24473d69284e97bcdd7ecc0887adb82044591b85a7f717`, and the training Namespace passed server dry-run. The approved `istioctl install -f k8s/istio-training/istio-profile.yaml --verify` completed. The `istiod` Deployment and Pod reported Ready, with no Pod restarts; 15 Istio CRDs, the expected injection and validation webhooks, and no Istio/ztunnel DaemonSet were observed. The previously checked Loki and Alloy workloads and all nodes remained Ready.

The installer warned that Calico's `bpfConnectTimeLoadBalancing=TCP` should be disabled. Read-only inspection showed Calico's Linux dataplane is `Iptables`, Felix `bpfEnabled=false`, and kube-proxy Ready on all four nodes. Tigera describes this warning as not preventing basic functionality; its production BPF recommendation does not justify a cluster-wide Felix change in this non-BPF pilot. Recheck the dataplane before any future BPF-mode deployment. This checkpoint verifies the control plane only; it does not validate injection or traffic through sidecars.

## Reproduction

The upstream `istioctl-1.31.1-linux-amd64.tar.gz` release asset was verified against the release SHA-256 `a44563904f22f2a8bf6ac4fff1b0bad9f718587c2be6aa807b83fe9049910639`. The initial manifest generation used no kubeconfig or cluster. Commands:

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

Before proceeding to the training gate, inspect the actual control-plane image identity and webhook selectors, confirm the existing workloads remain healthy, and server dry-run/diff the exact training resources in dependency order. Namespaced workloads can be server dry-run only after approved creation of their namespace. One `istiod` replica makes injection unavailable while it is down; avoid starting or replacing training Pods during that outage. Training namespace creation, workload changes, injection, and cleanup must be separately reviewed.

For removal, delete training workloads and opt-in labels first, then uninstall the exact Istio installation after verifying no other control plane depends on its shared resources. Upstream documents `istioctl uninstall --purge` for complete removal but warns that it deletes cluster-scoped resources potentially shared by other control planes. Inspect remaining webhooks, roles, CRDs, Pods, and namespaces after removal. This is a procedure to review, not authorization to execute it.

Official references: [Istio 1.31.1 release](https://github.com/istio/istio/releases/tag/1.31.1), [minimal profile](https://istio.io/latest/docs/setup/additional-setup/config-profiles/), [manifest generation](https://istio.io/latest/docs/reference/commands/istioctl/), [sidecar privileges and Istio CNI](https://istio.io/latest/docs/setup/additional-setup/cni/), [Pod Security Admission](https://istio.io/latest/docs/setup/additional-setup/pod-security-admission/), [Calico BPF warning](https://docs.tigera.io/calico/latest/network-policy/istio/app-layer-policy#warning-about-bpf-load-balancing), [uninstall guidance](https://istio.io/latest/docs/setup/install/istioctl/).
