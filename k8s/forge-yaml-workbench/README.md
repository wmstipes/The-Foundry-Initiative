# Forge YAML Workbench Kubernetes Manifests

These manifests define the deployed SignalForge browser-local Forge YAML Workbench.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Version:

```text
0.5.0
```

Immutable image reference:

```text
wmstipes/signalforge-yaml-workbench:0.5.0@sha256:11e8fcc4989fe7dcdc1c5312786b80189a98b6a9acb82e979aa8235d756fcb8e
```

The published OCI image index contains active `linux/amd64` and `linux/arm64` manifests. No floating image tag is used. The tracked Deployment and live cluster use immutable `0.5.0`. Local `0.5.1` source corrects finding-navigation scrolling but is not staged here until an immutable patch image is separately approved and published.

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

The live `0.5.0` deployment has one available Ready replica with zero restarts and a runtime ImageID matching OCI index digest `sha256:11e8fcc4989fe7dcdc1c5312786b80189a98b6a9acb82e979aa8235d756fcb8e`. NodePort `30081`, its ready EndpointSlice, `/healthz`, the application page response, Content Security Policy, and `X-Content-Type-Options` passed runtime verification. Interactive browser acceptance confirmed the OWASP profile and General YAML isolation, then found a finding-navigation scroll defect corrected in local `0.5.1` source.
