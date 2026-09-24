# Istio learning exercise — source-only candidate

This directory is a review package, **not** an apply-all directory. It has not
been deployed or server dry-run against SignalForge. The separate
[offline control-plane review](../../docs/milestones/istio-minimal-offline-review.md)
records the broad RBAC, webhooks, CRDs, 2 GiB istiod request and one-replica
choice. The cluster-wide permission decision, exact images and uninstall
procedure need approval before any installation.

`istio-profile.yaml` is an `istioctl` input, not a resource for `kubectl apply`.
It chooses the minimal sidecar profile with control-plane autoscaling disabled.
The rendered manifest contains one istiod Deployment (500m CPU and 2,048 MiB
requested), 15 CRDs, cluster-wide RBAC and admission webhooks. It does **not**
create `istio-system` as a Namespace or limit istiod's broad permissions to the
training namespace. Do not assume an install is namespace-only.
The rendered injector values request 100m CPU and 128 MiB per sidecar proxy,
with limits of 2 CPU and 1 GiB each. Two training Pods add at least 200m CPU
and 256 MiB of proxy requests beyond the 500m/2 GiB control plane and small
application containers. Compare the actual admitted Pod specs and measured
usage with these assumptions.

## Reviewed scope

- `namespace.yaml` creates only `forge-mesh-training`, initially with
  `istio-injection=disabled` and Pod Security `baseline`. The separate
  `privileged` admission exception needed for non-CNI sidecar init containers
  is **not** in source and needs an explicit live gate.
- `workloads.yaml` contains one ServiceAccount with automatic token mount
  disabled, one BusyBox HTTP server Deployment, an internal ClusterIP Service,
  and one BusyBox client Deployment. Both application containers run as
  non-root with a read-only root filesystem, bounded requests/limits, dropped
  capabilities, and no persistent storage. Istio's injected proxy will need
  its own projected identity token; confirm the admitted Pod has that
  projection while the application container has no default token.
- The BusyBox index `sha256:bdf57e528e45e4433820e045b29b4597825a1c9e38353532d90a01445013f82e`
  was already reviewed for Linux ARM64 in the Loki recovery work. Reconfirm
  registry availability and inspect the actual child digest at installation.
  The operator separately observed Linux ARM64 for Istio 1.31.1 `pilot` and
  `proxyv2`; reconcile the exact rendered/pulled image digests before install.
- This candidate intentionally has no NetworkPolicy; a ClusterIP is reachable
  by other in-cluster Pods unless other policy applies. Do not confuse a
  separate namespace with network isolation. Keep test traffic strictly
  between these disposable workloads; review whether a policy is required
  before any longer-running trial.

## Offline review gate

With the exact Istio 1.31.1 CLI, from the repository root, generate the full
control-plane manifest into an off-repo review directory:

```powershell
$reviewDir = Join-Path $env:USERPROFILE 'SignalForge-Istio-Review'
New-Item -ItemType Directory -Path $reviewDir -Force | Out-Null
& '<verified path to istioctl.exe>' manifest generate -f .\k8s\istio-training\istio-profile.yaml `
  --output (Join-Path $reviewDir 'istio-minimal-1.31.1.yaml')
if ($LASTEXITCODE -ne 0) { throw 'Istio render failed' }
Get-FileHash (Join-Path $reviewDir 'istio-minimal-1.31.1.yaml') -Algorithm SHA256
```

Review every rendered object, image, service account/ClusterRoleBinding,
webhook selector and failure policy, control-plane resource request, and
namespace precondition. Compare the generated document's object set and
profile settings to the offline review. Review `namespace.yaml` and
`workloads.yaml` independently. Only after source review, use server dry-run
and `kubectl diff` for the exact resources under an explicit admission gate.
No install or `kubectl apply` is part of this offline step.

## Proposed later live sequence — each mutation separately gated

1. Verify expected context, four Ready nodes, current capacity, existing
   workloads, Calico, no Istio control plane/webhooks, and absence of the
   training namespace. Capture existing application and logging baseline.
   Stop if this state differs.
2. Review the `istio-system` Namespace and exact rendered CRDs, RBAC and
   webhooks. Only with explicit install approval use the reviewed IstioOperator
   input and exact CLI version. Confirm one Ready istiod, the expected
   admission selectors, no CNI DaemonSet/gateway/ztunnel, and no changes to
   existing Pods or namespaces. Stop and diagnose if any check fails.
3. In a separate approved training gate, server dry-run/diff and apply
   `namespace.yaml`, then server dry-run/diff and apply `workloads.yaml`.
   Wait for both Deployments and confirm each Pod contains only its application
   container. Record Pod IDs and at least ten successful internal requests:

   ```powershell
   kubectl --context kubernetes-admin@kubernetes -n forge-mesh-training `
     exec deployment/mesh-client -c client -- wget -qO- http://mesh-server:8080/
   ```

4. In another explicit gate, confirm **only** `forge-mesh-training` is to be
   meshed. Review the Pod Security tradeoff, then change that namespace to
   `pod-security.kubernetes.io/enforce=privileged` and
   `istio-injection=enabled`. Scale only the two training Deployments down to
   zero and back to one so new Pod IDs are admitted with sidecars. Confirm
   two containers per Pod, istio-init completion, one Ready istiod, proxy
   synchronization, no regression of the baseline workloads, and ten more
   successful requests. Record `kubectl top pod --containers` for the two
   training Pods and istiod. These observations show injection and successful
   requests; they do not by themselves prove mTLS, production performance, or
   NetworkPolicy enforcement. Do not enable injection on existing namespaces.

## Stop and return

- If training admission, injection or requests fail, stop changes and inspect
  only the new namespace and istiod logs/events. Keep the original application
  and observability workloads untouched. Do not repeatedly restart existing
  Pods to get a successful demo.
- To return the disposable workloads to their unmeshed baseline, first scale
  **only** the two training Deployments to zero. Set training namespace
  `istio-injection=disabled` and Pod Security `enforce=baseline` before scaling
  them back to one. Verify fresh Pod IDs, one container each, and the same
  internal response. Merely changing a label does not remove a sidecar from
  an existing Pod.
- After final evidence, remove only the training namespace and verify it is
  gone. Inventory other Istio control planes and their resources before an
  explicitly approved `istioctl uninstall --purge`; upstream warns that purge
  deletes shared cluster-scoped objects. Verify Istio webhooks, roles, CRDs,
  Pods and `istio-system` afterward, and remove `istio-system` only if its
  ownership is confirmed. Do not run `kubectl delete -f` on the full rendered
  CRD bundle as a shortcut.

An installed pilot is accepted only if the baseline and meshed checks pass,
existing workloads remain healthy, the capacity and permissions are acceptable
in measured practice, and the separately approved return path completes. An
offline manifest hash or a Ready control plane alone does not meet that gate.

Official references: [sidecar injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/), [Pod Security Admission with Istio](https://istio.io/latest/docs/setup/additional-setup/pod-security-admission/), and [uninstall warning](https://istio.io/latest/docs/setup/install/istioctl/).
