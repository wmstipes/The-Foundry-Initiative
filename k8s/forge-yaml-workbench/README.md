# Forge YAML Workbench Kubernetes Manifests

These manifests define the deployed SignalForge browser-local Forge YAML Workbench.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Version:

```text
0.4.1
```

Immutable image reference:

```text
wmstipes/signalforge-yaml-workbench:0.4.1@sha256:96c715c938f1636686190e294829c61f0f7af71117b353bd2df05a9fc67bddf2
```

The OCI image index contains active `linux/amd64` and `linux/arm64` manifests. No floating image tag is used. The live cluster and tracked Deployment both use the accepted immutable `0.4.1` correction.

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

The live `0.4.1` deployment has one available Ready replica with zero restarts and a runtime ImageID matching OCI index digest `sha256:96c715c938f1636686190e294829c61f0f7af71117b353bd2df05a9fc67bddf2`. NodePort `30081`, its ready EndpointSlice, `/healthz`, the application page response, Content Security Policy, and `X-Content-Type-Options` passed runtime verification. Repeated interactive browser acceptance confirmed Kubernetes and General YAML behavior, schema result boundaries, and strict-CSP startup.
