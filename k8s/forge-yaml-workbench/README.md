# Forge YAML Workbench Kubernetes Manifests

These manifests define the deployed SignalForge browser-local Forge YAML Workbench.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Tracked deployment release:

```text
0.8.0
```

Immutable tracked candidate image reference:

```text
wmstipes/signalforge-yaml-workbench:0.8.0@sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3
```

The published OCI index contains active `linux/amd64` manifest `sha256:dfbfc92e3d4a074d0a421cc3fdb7937f4288937af291aac71ec9a0dc3786d536` and `linux/arm64` manifest `sha256:2db1d88fe7357452f82256e81a4d56ef52d3ddc72bffe0f31524adab524ce615`. The additional unknown-platform entries are BuildKit attestation manifests linked to those images. No floating image tag is used.

The tracked Deployment now stages accepted immutable `0.8.0`. The live cluster remains on `0.7.0` until the Deployment-only rollout is separately reviewed and approved.

## Security and data boundaries

- The namespace enforces the Kubernetes restricted Pod Security Standard at v1.36.
- The Pod runs as non-root with runtime-default seccomp.
- Privilege escalation is disabled, all Linux capabilities are dropped, and the root filesystem is read-only.
- Only a bounded `emptyDir` at `/tmp` is writable.
- No ServiceAccount token is mounted and no Kubernetes API or RBAC access is granted.
- YAML analysis occurs in the browser. Pasted YAML is not sent to or stored by the NGINX container.

## Local validation

From the repository root:

```powershell
python .\scripts\validate-k8s-manifests.py
```

## Change review

Before any update, preview the exact resources against the live API without applying them:

```powershell
kubectl apply --dry-run=server -f .\k8s\forge-yaml-workbench\namespace.yaml
kubectl apply --dry-run=server -f .\k8s\forge-yaml-workbench\forge-yaml-workbench-deployment.yaml
kubectl apply --dry-run=server -f .\k8s\forge-yaml-workbench\forge-yaml-workbench-service.yaml
kubectl diff -f .\k8s\forge-yaml-workbench
```

Do not apply a change until the dry-run and diff are reviewed and explicit approval is given.

After approval, apply only the reviewed resource and verify the rollout. For a Deployment-only image update:

```powershell
kubectl apply -f .\k8s\forge-yaml-workbench\forge-yaml-workbench-deployment.yaml
kubectl rollout status deployment/forge-yaml-workbench -n forge-tools --timeout=180s
kubectl get deployment,pods,service -n forge-tools -o wide
```

Until the separately approved deployment occurs, the live `0.7.0` deployment has one available Ready replica with zero restarts and a runtime ImageID matching OCI index digest `sha256:f9f5939910382911b23e78609ea5690e617e2a446c3dd707da2c1c6852a8a6d2`. NodePort `30081`, its ready EndpointSlice, fresh HTTP 200 responses from `/healthz` and the application page, Content Security Policy, and `X-Content-Type-Options` passed runtime verification. Interactive browser acceptance confirmed the formatting preview, browser-local Kubernetes and General YAML Markdown reports, visible Copied and Downloaded states, predictable report filenames, mode isolation, cancellation, unchanged editor and unsaved state, the OWASP profile, and corrected finding-link scrolling.
