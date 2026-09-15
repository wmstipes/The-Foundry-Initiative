# Forge YAML Workbench Kubernetes Manifests

These manifests define the tracked SignalForge browser-local Forge YAML Workbench deployment.

## Resources

- `namespace.yaml` creates the restricted `forge-tools` namespace.
- `forge-yaml-workbench-deployment.yaml` runs one stateless, unprivileged NGINX replica on container port `8080`.
- `forge-yaml-workbench-service.yaml` provides lab access through NodePort `30081`.

## Image

Tracked deployment release:

```text
0.10.0
```

Immutable tracked image reference:

```text
wmstipes/signalforge-yaml-workbench:0.10.0@sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206
```

The published OCI index contains active `linux/amd64` manifest `sha256:c8223d013931e0c02a582f372b826cb827eed1d6f2ba887eac7661387ef03fa2` and `linux/arm64` manifest `sha256:a297014f6df7579c25bcaaa6bbea12bb39e398a36828d647228e5859e7b77869`. The additional unknown-platform entries are BuildKit attestation manifests linked to those images. No floating image tag is used.

The tracked Deployment is the immutable `0.10.0` deployment candidate. The live cluster remains on accepted immutable `0.9.0` until server-side dry-run and exact diff evidence are reviewed and cluster deployment is separately approved.

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

The live `0.9.0` deployment has one available Ready replica on `forge-node-03` with zero restarts and a runtime ImageID matching OCI index digest `sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581`. NodePort `30081`, its single ready EndpointSlice endpoint, fresh HTTP 200 responses from `/healthz` and the application page, Content Security Policy, and `X-Content-Type-Options` passed runtime verification. Interactive browser acceptance confirmed Tree search across keys, scalar values, and canonical paths; counted wrapping navigation; ancestor expansion; visual and active match states; keyboard and focus behavior; parser recovery; formatting and report isolation; and reset boundaries.
