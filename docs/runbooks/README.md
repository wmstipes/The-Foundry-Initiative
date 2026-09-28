# SignalForge operations index

**Reviewed:** 2026-09-28

This is the starting point for operating the existing cluster. Commands in
component runbooks can deploy, restart, or remove resources; use their named
procedure and prerequisites. Do not apply a whole `k8s` directory as a repair.

## Service access

| Service | Normal browser access | Kubernetes identity or data boundary | Operating guide |
| --- | --- | --- | --- |
| Forge portal | Private HTTPS | Static links; no cluster identity | [Gateway and portal](../../k8s/lan-portal/README.md) |
| YAML Workbench | Private HTTPS; no application login | Browser-local YAML processing; no API identity | [Workbench](../../k8s/forge-yaml-workbench/README.md) |
| Restaurant API | Private HTTPS | Application API; no user cluster inspection | [Restaurant](restaurant-api-operator-runbook.md) |
| Grafana | Private HTTPS and Grafana login | Queries Prometheus and Loki | [Grafana](../../k8s/grafana/README.md) |
| Prometheus | Private HTTPS and BasicAuth | Scoped workload discovery | [Prometheus](../../k8s/prometheus/README.md) |
| ForgeOps Console | Private HTTPS and BasicAuth | Shared read-only ServiceAccount; single operator scope | [Cluster Console](../../k8s/forgeops-console/README.md) |
| Headlamp | Private HTTPS, BasicAuth, then Dex OIDC | User RBAC: `view` and scoped Node reader | [Headlamp and identity](headlamp-oidc.md) |
| Service Pulse board | Private HTTPS and BasicAuth | Reads internal probe; no Kubernetes credentials | [Pulse](../../k8s/service-pulse/README.md) |

Dex supplies Headlamp identity; it is not yet a shared login service for the
other applications. Service Pulse's probe and Loki are internal services.
The earlier [local portal preview](../../apps/signalforge-portal/README.md)
is separate from the page deployed in Kubernetes. Restaurant and Workbench
NodePorts remain alternate private-lab HTTP paths. TLS terminates at Traefik.

## Routine read-only checks

From PowerShell in the intended kubeconfig context:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl get --raw=/readyz --request-timeout=5s --context $ctx
kubectl get nodes --context $ctx
kubectl top nodes --context $ctx
kubectl get deployment,statefulset -A --context $ctx
kubectl get pods -A --context $ctx
kubectl get certificate -n forge-gateway --context $ctx
```

Inspect the relevant service's EndpointSlices and recent Events when a check
fails. A Ready Pod alone does not prove browser login, backend connectivity,
data freshness, or retained history. Use the component's application checks.
Review log output before sharing it; read-only access does not redact secrets.

## Change and upgrade procedure

1. Inspect current revision, image, replica count, storage, and access path.
   Record the exact baseline and recovery artifact appropriate to the service.
2. Review the relevant manifest or Helm render, then server dry-run and diff
   the named resources. Keep private overlays and credentials outside Git.
3. Apply only the reviewed change within the authorized work. A repository
   merge does not apply cluster resources.
4. Wait for rollout, verify Service endpoints and application behavior, and
   recheck authentication and read/write boundaries when access changes.
5. Record the observed result and remaining limits. Retain the earlier
   configuration until the new state has been accepted.

Headlamp upgrades require both tracked base values and its private OIDC
overlay. Control-plane upgrades additionally require preserving the OIDC
settings through kubeadm configuration/patches; see [identity operations](headlamp-oidc.md).
The current single control plane can interrupt API access during replacement.

## Backup and recovery responsibilities

| Component | Retained state and accepted evidence | Remaining operator responsibility |
| --- | --- | --- |
| Prometheus | Head-local PV; off-node cold archive and isolated TSDB validation | Weekly manual backup; inspect helper retention; full service restore timing unmeasured |
| Grafana | Head-local PV; isolated recovery reached usable dashboards in 4.37 minutes | Weekly and pre-upgrade archives; preserve matching encryption key and credentials separately |
| Loki | Head-local PV; off-node backup, restart persistence, and isolated service restore accepted | Maintain backup freshness; naturally elapsed seven-day retention and elapsed recovery time remain open |
| Dex / Kubernetes identity | Kubernetes storage plus private configuration and client credentials | Preserve identity state with a reviewed cluster-state backup; full identity restore has not been tested |
| Private CA | Offline root backup; online intermediate and gateway leaf | Keep original root and passphrase protected; review intermediate/root expiry and client trust |
| Stateless apps | Reviewed manifests, images, and required configuration | Preserve exact versions and private inputs; a reinstall does not restore in-memory Pulse samples |

Follow the [Prometheus](../../k8s/prometheus/README.md),
[Grafana](../../k8s/grafana/README.md), [Loki](../milestones/loki-recovery-candidate.md),
and [PKI](../../k8s/private-pki/README.md) procedures. Their destructive or
interrupting steps are not routine health checks. A local PV with `Retain`
is not an off-node backup. Whole-cluster disaster recovery is not demonstrated
by the component restore tests.

## Other operating paths

- [Kubelet serving-certificate rotation](kubelet-serving-certificates.md)
- [ForgeOps read-only snapshots](forgeops-snapshot.md)
- [Istio learning and scoped route exercises](../../k8s/istio-lab/README.md)
- [Command helpers and their effects](../../scripts/README.md)
