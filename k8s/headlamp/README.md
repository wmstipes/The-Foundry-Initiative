# Headlamp cluster viewer

This is the read-only Headlamp 0.45.0 pilot in `forge-headlamp`. The Helm
release is named `headlamp`. The UI is reachable only through a local
port-forward to its ClusterIP Service. It has no PVC or ingress. The namespace
enforces the Kubernetes v1.36 restricted Pod Security profile. The pod requests
50m CPU and 128Mi memory and is capped at 300m CPU and 512Mi memory.

## Reconcile the reviewed configuration

From the repository root in PowerShell, with Helm installed and the Headlamp
chart repository added (`helm repo add headlamp
https://kubernetes-sigs.github.io/headlamp/`):

```powershell
$ctx = 'kubernetes-admin@kubernetes'
kubectl apply -f .\k8s\headlamp\namespace.yaml --context $ctx
helm upgrade --install headlamp headlamp/headlamp `
  --version 0.45.0 --namespace forge-headlamp --kube-context $ctx `
  --values .\k8s\headlamp\values.yaml `
  --wait --timeout 5m --rollback-on-failure
kubectl apply -f .\k8s\headlamp\node-reader.yaml --context $ctx
```

The Helm chart creates the ServiceAccount and a ClusterRoleBinding whose
`roleRef.name` must be `view`. The chart names that binding `headlamp-admin`
even though it grants `view`; check `roleRef`, not the object name. The separate
`node-reader.yaml` provides only `get/list/watch` on Nodes because the
Kubernetes built-in `view` role does not grant node listing in this cluster.
The existing Metrics Server and `view` role supply read access to pod and node
resource metrics. Never install the chart with its default `cluster-admin`
binding, and keep `config.unsafeUseServiceAccountToken` false.

## Verify and open

```powershell
$sa = 'system:serviceaccount:forge-headlamp:headlamp'
kubectl get deployment,pods,service -n forge-headlamp --context $ctx
kubectl auth can-i list nodes --as $sa --context $ctx
kubectl auth can-i list pods --all-namespaces --as $sa --context $ctx
kubectl auth can-i get secrets --all-namespaces --as $sa --context $ctx
kubectl auth can-i create deployments -n forge-restaurant --as $sa --context $ctx
kubectl port-forward service/headlamp 8080:80 `
  --namespace forge-headlamp --context $ctx
```

The four authorization answers should be `yes`, `yes`, `no`, `no`. In a
second PowerShell window, create a short-lived token and copy it without
printing it to the terminal:

```powershell
kubectl create token headlamp --namespace forge-headlamp `
  --context kubernetes-admin@kubernetes --duration=1h | Set-Clipboard
```

Visit `http://127.0.0.1:8080` and paste the token into the login screen.
Do not commit or share the token. The pilot displayed four Ready nodes,
workloads, CPU/memory usage, and an initial Headlamp readiness-probe Event.
That single startup Event was observed while the pod subsequently became
Ready; the pilot does not establish long-term uptime or log persistence.

## Reversal

```powershell
helm uninstall headlamp --namespace forge-headlamp --kube-context $ctx
kubectl delete -f .\k8s\headlamp\node-reader.yaml --context $ctx
```

Keep the namespace for review or remove it separately after checking it
contains no other resources. The pilot does not expose Headlamp through TLS
or an ingress; a future shared endpoint needs an authentication and certificate
design before exposure.
