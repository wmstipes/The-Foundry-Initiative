# Istio learning lab: route, break, diagnose, repair

This is a guided lab, not an apply-all directory. Keep the current minimal
Istio control plane installed while learning. Only `forge-mesh-lab` may opt
into injection. Do not change the restaurant, pulse, observability, tools,
system, or Calico namespaces. Do not apply `route-stable.yaml`,
`route-canary.yaml`, and `route-fault.yaml` together: they replace the **same**
VirtualService in sequence.

## What the pieces do

| Component | Job | Observe with |
| --- | --- | --- |
| Kubernetes `Service/lab-api` | Finds both healthy API Pods using `app=lab-api` | `kubectl -n forge-mesh-lab get endpointslices -l kubernetes.io/service-name=lab-api` |
| Istio `DestinationRule/lab-api` | Defines `v1` and `v2` subsets from Pod labels | `kubectl -n forge-mesh-lab get destinationrule lab-api -o yaml` |
| Istio `VirtualService/lab-api` | Sends traffic to one or both subsets; can abort `/break` | `kubectl -n forge-mesh-lab get virtualservice lab-api -o yaml` |
| `istio-proxy` in each Pod | Carries the request and receives route config from `istiod` | `istioctl proxy-status`, `istioctl proxy-config routes` |
| Prometheus and Grafana | Scrape the three lab proxies and graph version, response code, latency, and collection health | Grafana: **SignalForge Istio Learning Lab** |

There is no gateway, NodePort, production routing change, lab persistent storage,
or NetworkPolicy. `lab-api` is a ClusterIP reachable from other cluster Pods;
this namespace is for short, disposable exercises, not network isolation.
The three pinned BusyBox application containers have 10m CPU/16Mi memory
requests each; injected proxies request more resources. Without Istio CNI,
the sidecar init step needs a temporary Pod Security `privileged` exception
for this namespace. Keep that exception only during an active lab session.

## Stage 1: ordinary Kubernetes traffic

Start with `namespace.yaml`: injection disabled, Pod Security baseline.
Server dry-run and create the Namespace, then server dry-run and apply
`workloads.yaml` after the Namespace exists. Its two server Deployments
return `v1` and `v2`; the Service selects both; the client calls the Service.
Wait for all three Deployments and record their Pod IDs. Run several requests:

```powershell
$ctx = 'kubernetes-admin@kubernetes'
$lab = 'forge-mesh-lab'
if ((kubectl config current-context).Trim() -ne $ctx) { throw 'Context differs; stop.' }
if (kubectl --context $ctx get namespace $lab --ignore-not-found -o name) {
  throw 'Lab namespace already exists; stop and inspect.'
}
kubectl --context $ctx create --dry-run=server -f .\k8s\istio-lab\namespace.yaml
if ($LASTEXITCODE -ne 0) { throw 'Namespace dry-run failed.' }
kubectl --context $ctx apply -f .\k8s\istio-lab\namespace.yaml
if ($LASTEXITCODE -ne 0) { throw 'Namespace creation failed.' }
kubectl --context $ctx apply --dry-run=server -f .\k8s\istio-lab\workloads.yaml
if ($LASTEXITCODE -ne 0) { throw 'Workload dry-run failed.' }
kubectl --context $ctx apply -f .\k8s\istio-lab\workloads.yaml
if ($LASTEXITCODE -ne 0) { throw 'Workload creation failed.' }
foreach ($name in 'lab-api-v1','lab-api-v2','lab-client') {
  kubectl --context $ctx -n $lab rollout status "deployment/$name" --timeout=5m
  if ($LASTEXITCODE -ne 0) { throw "Rollout failed: $name" }
}
1..10 | ForEach-Object {
  $version = kubectl --context $ctx -n $lab exec deployment/lab-client -c client -- `
    wget -qO- http://lab-api:8080/
  if ($LASTEXITCODE -ne 0 -or $version.Trim() -notin @('v1','v2')) {
    throw "Baseline request $_ failed; stop."
  }
  $version
}
```

Predict: responses can contain both versions, since Kubernetes distributes
requests across the two ready endpoints. Verify there is one application
container and no `istio-proxy` in each Pod. There is no Istio route yet.

## Stage 2: opt in only this namespace

In a separately reviewed live gate, scale **only** these three Deployments to
zero and wait until their Pods are gone. Change **only** this Namespace to
`pod-security.kubernetes.io/enforce=privileged` and
`istio-injection=enabled` in one label operation, then scale them back to one.
Confirm three Pods Ready, `istio-init` completed, and `istio-proxy` Ready and
connected to `istiod` in `istioctl proxy-status`.

Istio 1.31 can place the proxy as a **restartable init container** with
`restartPolicy: Always`. Do not insist on `spec.containers.Count -eq 2`:
inspect both `spec.containers` and `spec.initContainers` as well as their
status arrays. A Ready count of `2/2` may include the application and native
sidecar. Record the proxy image ID from the appropriate status array.

Run requests again. At this point sidecars are present, but Kubernetes still
distributes calls among both versions because there is no VirtualService.
The presence of sidecars alone does not prove mTLS, availability, or policy.

## Stage 2b: observe the meshed lab

The existing Forge Prometheus initially collects **no** Istio metrics. From
the reviewed checkout, validate `metrics-services.yaml` with a server dry-run
and apply it only after the three proxies are Ready. Its three ClusterIP
Services select the client, v1, and v2 Pods separately and expose only their
Envoy `:15090/stats/prometheus` endpoint to cluster Pods. The endpoint is
cleartext and is **not** an access-controlled interface; use this only for
the short-lived lab. This does not add a new Prometheus RBAC permission or
install a second collector.

Before changing central monitoring, compare the live
`forge-observability/prometheus-config` data to the tracked source: the
Restaurant API job and alert rules must already match; the only intended
change is a static `istio-lab` job for those three Services. Capture the live
ConfigMap to a local rollback file outside Git. Validate the new embedded
Prometheus config with `promtool check config` and inspect `kubectl diff`.
Then apply **only** `k8s/prometheus/prometheus-config.yaml` and restart
**only** `deployment/prometheus` (the server does not enable HTTP reload).
Wait for Ready, verify the three new targets report `up == 1`, and verify
the three Restaurant API targets and their alerts remain present. If the
rollout or Restaurant target check fails, restore the saved ConfigMap and
restart only Prometheus; inspect target errors before trying again. This
step briefly interrupts collection during the `Recreate` rollout.

The third dashboard is
`k8s/grafana/dashboards/signalforge-istio-lab.json`. Review the live
`grafana-dashboards` ConfigMap and preserve it locally before generating a
new one from the tracked `k8s/grafana/dashboards` directory. Diff, then
apply **only** the dashboard ConfigMap; Grafana polls projected files every
30 seconds, so no Grafana restart is needed. Verify the two pre-existing
dashboards still load and the new **SignalForge Istio Learning Lab** dashboard
has six panels. If provisioning differs from the checked-in files, stop and
review rather than overwriting operator changes. The Grafana test script
expects three dashboards after this phase. A ConfigMap rollback restores the
prior dashboards; no database wipe is involved.

Generate several requests after the collector is Ready; allow at least two
30-second scrapes, and keep requests flowing for a five-minute `rate` window
before interpreting the traffic and latency panels. Check **Proxy scrape
health** first. The **Requests by destination version** panel uses server
reporters; **Client responses by code** and **Client 503 responses** use the
source reporter because the injected `/break` abort can happen before any
server sees it. The panel shows an expected 503 in this exercise, not a
production incident. `No data` means no series or too few samples, not a
healthy zero. The v1/v2 split is probabilistic, especially with few requests.

Use the Grafana dashboard beside `kubectl` and `istioctl` while carrying out
stages 3 and 4. If `up` is zero, investigate Services, EndpointSlices, and
the Prometheus target error before using the traffic panels as evidence. If
`up` is one but an injected fault is not visible, query the client proxy
directly and check the source reporter and live VirtualService. Grafana
visualizes metrics and complements the request and proxy-config checks.

## Stage 3: choose a version and shift traffic

Apply `route-stable.yaml`: it creates the DestinationRule and the stable
VirtualService. Server dry-run the file first. Predict and test that 10
requests to `/` return only `v1`. If a result differs, check proxy status,
the Service endpoints, and the live VirtualService before proceeding.

Apply **only** `route-canary.yaml` next. It replaces the VirtualService with
50/50 weights and keeps the DestinationRule. Request `/` 30 times and count
the `v1` and `v2` responses. The exact counts are random; both versions
should appear. Compare this with the unchanged Kubernetes Service and
Deployments to see what the mesh changed.

## Stage 4: break one request path on purpose

Apply **only** `route-fault.yaml` after a successful server dry-run. Its first
rule aborts `/break` with HTTP 503 for 100% of requests; its second rule keeps
normal `/` requests on the 50/50 split. This is a client-facing failure
created by Envoy configuration, not a broken application Pod. Test both paths:

```powershell
kubectl --context $ctx -n $lab exec deployment/lab-client -c client -- `
  wget -S -O - http://lab-api:8080/break
# A nonzero exit and HTTP 503 are expected for this single command.
kubectl --context $ctx -n $lab exec deployment/lab-client -c client -- `
  wget -qO- http://lab-api:8080/
```

Diagnose before repairing: check both server Pods and the Service endpoint
slices, then inspect `VirtualService/lab-api` for the `/break` fault. Run
`istioctl proxy-status` and `istioctl proxy-config routes` on the client Pod
to distinguish configuration distribution from application health. A
successful `istioctl analyze -n forge-mesh-lab` does not mean an intentional
503 fault is absent. To repair, apply `route-canary.yaml` again and confirm
normal `/` responses. Record the before/after VirtualService and client
response. Leave unrelated workloads alone.

## Return or continue later

At session end, apply `route-stable.yaml` (known good), scale only the three
lab Deployments to zero, wait for Pods to disappear, then set the lab
Namespace to `istio-injection=disabled` and Pod Security `baseline` before
scaling them back to one. Verify new Pod IDs, no injected proxy, and ordinary
service responses. Remove `metrics-services.yaml` Services at the end of the
meshed session. The static lab Prometheus job will show three failed targets
until you restore the previously captured ConfigMap and restart Prometheus;
verify Restaurant API targets again. The Grafana dashboard can remain as a
historical view, but will show no current lab traffic. The Istio control
plane can remain for another lesson;
opt into injection again only when actively testing.

If any stage fails, stop changes and inspect the lab Pods, events, endpoint
slices, VirtualService, DestinationRule, and `istiod` without mutating other
namespaces. Do not run `istioctl uninstall --purge` as a recovery shortcut.
Delete the lab Namespace only when the exercise is finished and its ownership
has been checked. Control-plane uninstall remains a separate decision.

References: [traffic shifting](https://istio.io/latest/docs/tasks/traffic-management/traffic-shifting/),
[fault injection](https://istio.io/latest/docs/tasks/traffic-management/fault-injection/),
[sidecar injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/),
[Kubernetes native sidecars](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/).
