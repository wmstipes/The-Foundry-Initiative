# Forge YAML Workbench Kubernetes Manifests

These manifests define the deployed SignalForge browser-local Forge YAML Workbench.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Version:

```text
0.4.0
```

Immutable image reference:

```text
wmstipes/signalforge-yaml-workbench:0.4.0@sha256:96e3d8e4a1b563d5d719521bbd8f0d5f6f3e3a5fc3a299851d21186a20de3477
```

The OCI image index contains both `linux/amd64` and `linux/arm64`. No floating image tag is used. The manifest stages the published immutable `0.4.0` image for server-side dry-run and live diff review; the live cluster remains on `0.3.0` until deployment is separately approved.

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

The accepted live `0.3.0` deployment has one available Ready replica with zero restarts and a runtime ImageID matching OCI index digest `sha256:3abd4292f6cbd506dbc976924d2b61cf8093a7653e02654efaedc207e3f3086f`. NodePort `30081`, its ready EndpointSlice, `/healthz`, the application page, mode markers, Content Security Policy, and `X-Content-Type-Options` passed immediate runtime verification. Live browser acceptance confirmed Kubernetes as the default, content-preserving mode switches, suppression of Kubernetes-only findings in General YAML, and mapping, sequence, scalar and explicit null roots.
