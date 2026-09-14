# Forge YAML Workbench Kubernetes Manifests

These manifests define the deployed SignalForge browser-local Forge YAML Workbench.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Tracked deployment release:

```text
0.6.0
```

Immutable deployed image reference:

```text
wmstipes/signalforge-yaml-workbench:0.6.0@sha256:4166df67190eaaade054be09c91f0ef8a76e832f290f7383fc4e58c7dd7469bc
```

The published OCI index contains active `linux/amd64` manifest `sha256:f051ce44976c1abdd2076415edc6476ef57cb8c5e2c7cb196cb1391616ab5f0a` and `linux/arm64` manifest `sha256:d5795e44b4553b8bd6b8a96c7ad6e3b574e8b9e7dcdbc80c0ed1f34ef2e01208`. The additional unknown-platform entries are BuildKit attestation manifests linked to those images. No floating image tag is used.

The tracked Deployment and live cluster both use accepted immutable `0.6.0`. The Deployment-only rollout followed successful manifest validation, server-side dry-run, live diff review, and explicit approval.

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

The live `0.6.0` deployment has one available Ready replica with zero restarts and a runtime ImageID matching OCI index digest `sha256:4166df67190eaaade054be09c91f0ef8a76e832f290f7383fc4e58c7dd7469bc`. NodePort `30081`, its ready EndpointSlice, fresh HTTP 200 responses from `/healthz` and the application page, Content Security Policy, and `X-Content-Type-Options` passed runtime verification. Interactive browser acceptance confirmed the formatting preview, unchanged editor state before Apply, Cancel preservation, Apply formatting, invalid-YAML validation behavior, Kubernetes and General YAML modes, the OWASP profile, and corrected finding-link scrolling.
