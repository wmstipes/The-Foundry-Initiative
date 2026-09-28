# Kubernetes Manifests

SignalForge Kubernetes resources are grouped by workload.

## Restaurant API

Path: `k8s/fastapi-restaurant`

This directory contains the `forge-restaurant` namespace, Restaurant API configuration, Deployment, internal Service, and NodePort Service.

## Lightweight Prometheus

Path: `k8s/prometheus`

This directory contains the `forge-observability` namespace, least-privilege Pod-discovery RBAC, Prometheus configuration, Deployment, and internal Service.

## Kubernetes Metrics Server

Path: `k8s/metrics-server`

This directory contains the pinned Metrics Server v0.9.0 workload, upstream RBAC, internal Service, and aggregated API registration. The deployment validates every kubelet serving certificate with the Kubernetes service-account CA and does not use `--kubelet-insecure-tls`.

## Forge YAML Workbench

Path: `k8s/forge-yaml-workbench`

This directory contains the restricted `forge-tools` namespace, hardened stateless Workbench Deployment, and NodePort Service on `30081`. The live workload and tracked Deployment use accepted immutable `0.10.0`, including safe browser-local YAML file drop and the earlier corrected finding-navigation scrolling. The Workbench has no Kubernetes API identity or mounted ServiceAccount token and processes YAML only in the browser.

## Service Pulse

Path: `k8s/service-pulse`

This directory contains the restricted `forge-pulse` namespace, one live probe and one live board Deployment, and their internal ClusterIP Services. Both pin the published `0.1.1` OCI digest. The board is linked from the portal through a BasicAuth-protected private HTTPS route; the probe remains internal. See its README for workload evidence and scoped rollback. The protected route and policy are operated separately from the workload.

## Grafana and central logging

Paths: `k8s/grafana` and `k8s/central-logging`

Grafana provides the existing Prometheus dashboards and a provisioned Loki datasource. Alloy reads Service Pulse Pod logs with namespace-scoped permissions and sends them to a private, persistent Loki instance. The [central logging rollout record](central-logging/README.md) documents observed ingestion, Grafana queries, and log retrieval after a probe Pod replacement. It also records the remaining Loki persistence, retention, and recovery checks. Follow the reviewed per-resource procedure; do not apply the central logging directory wholesale or rerun its storage preparation.

## Istio learning lab

Path: `k8s/istio-lab`

The [guided lab](istio-lab/README.md) uses an isolated namespace, two versions
of a small HTTP service, and one client to explore sidecar injection, traffic
shifting, a scoped HTTP fault, diagnosis, and repair. The client makes one
request every 15 seconds so the Grafana panels remain useful between lessons.
Its route files represent alternative states of the same VirtualService; apply
them one at a time. Keep the healthy meshed lab running for later exploration.

## Headlamp cluster viewer

Path: `k8s/headlamp`

The [read-only Headlamp pilot](headlamp/README.md) pins Helm chart 0.45.0 and uses a restricted namespace, a ClusterIP Service, and a BasicAuth-protected private HTTPS route. The normal login is through privately configured Dex OIDC. The chart ServiceAccount and the signed-in user have separate read-only RBAC; the private OIDC overlay is required on upgrades. The runbook distinguishes live acceptance from the older port-forward/token recovery path.

## Private LAN portal and gateway

Path: `k8s/lan-portal`

MetalLB and Traefik provide a LAN-only HTTPS entry point. The two-replica Forge portal also links to the protected Headlamp and Service Pulse board. The [private-PKI runbook](private-pki/README.md) covers the offline root, gateway intermediate, and wildcard leaf. The laptop browser trusts the public root; NUC setup remains deferred. The gateway and single control plane are not highly available.

## ForgeOps Console cluster pilot

Path: `k8s/forgeops-console`

The [cluster runbook](forgeops-console/README.md) covers the `0.1.1` digest-pinned image, restricted single replica, read-only ServiceAccount, Traefik-only ingress policy, distinct BasicAuth gate, and observed rollout and browser checks. The workstation preview retains its separate loopback-only kubeconfig mode.

## Validation

From the repository root:

```powershell
python .\scripts\validate-k8s-manifests.py
```

CI also runs `promtool check config` against the Prometheus configuration embedded in its ConfigMap.
