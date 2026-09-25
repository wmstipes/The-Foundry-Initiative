# Istio learning lab: route, break, diagnose, repair

This is a persistent learning lab, not an apply-all directory. Keep the current minimal
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
the namespace does not provide network isolation. The three metrics Services
expose cleartext Envoy statistics on port 15090 within the cluster. Keep other
workloads out of this namespace and do not treat it as a security boundary.
The three pinned BusyBox application containers have 10m CPU/16Mi memory
requests each; injected proxies request more resources. Without Istio CNI,
the sidecar init step needs a Pod Security `privileged` exception
for this namespace. Keeping the lab meshed also keeps its namespace at
`pod-security.kubernetes.io/enforce=privileged`; inspect this label before
applying new workloads to the lab. The audit and warn labels remain restricted.

## Stage 1: ordinary Kubernetes traffic

For a new lab only, start with `namespace.yaml`: injection disabled, Pod Security
baseline. This file is a bootstrap manifest; **do not reapply it to the running
meshed lab**, because it would change the namespace injection and admission labels.
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
requests across the two ready endpoints. The client also makes one request to
`http://lab-api:8080/` every 15 seconds and logs only failed requests. It
never calls `/break`. Verify there is one application
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

For a new lab, the existing Forge Prometheus initially collects **no** Istio metrics. From
the reviewed checkout, validate `metrics-services.yaml` with a server dry-run
and apply it only after the three proxies are Ready. Its three ClusterIP
Services select the client, v1, and v2 Pods separately and expose only their
Envoy `:15090/stats/prometheus` endpoint to cluster Pods. The endpoint is
cleartext and is **not** an access-controlled interface; leave only the three
lab Services exposed internally. This does not add a new Prometheus RBAC permission or
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

The client supplies steady traffic after the collector is Ready. Allow at least two
30-second scrapes and a five-minute `rate` window
before interpreting the traffic and latency panels. Check **Proxy scrape
health** first. The **Requests by destination version** panel uses server
reporters; **Client responses by code** and **Client 503 responses** use the
source reporter because the injected `/break` abort can happen before any
server sees it. The panel shows an expected 503 in this exercise, not a
production incident. `No data` means no series or too few samples, not a
healthy zero. **Client 503 responses (total)** reads the client proxy's raw
counter: it can show the first five errors even when all happened before the
first Prometheus scrape of the new 503 series. It stays at five after repair
until the proxy restarts; zero or missing data alone does not prove recovery.
Confirm recovery by inspecting the VirtualService and making fresh successful
requests. The v1/v2 split is probabilistic, especially with few requests.

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

## Leave the lab ready for later

Keep the three Deployments at one replica, the namespace injection enabled,
the three metrics Services present, and the Prometheus job active. Leave
`route-canary.yaml` applied for a healthy 50/50 split. The client generates
about four requests per minute (roughly 5,760 per day), all to `/`. Its
application container requests 10m CPU and 16Mi memory and is limited to
100m CPU and 64Mi memory; the injected proxy uses additional resources.
Check `kubectl -n forge-mesh-lab logs deployment/lab-client -c client --tail=20`
for failures. The Grafana **SignalForge Istio Learning Lab** dashboard will
show fresh traffic after the five-minute rate window fills. A successful
request to `/` does not establish that a deliberate `/break` fault has been
removed; inspect the VirtualService after every fault exercise.

To restore the known good route after a fault, apply **only**
`k8s/istio-lab/route-canary.yaml`, inspect the live VirtualService to ensure
it has no `/break` abort, and make fresh requests to `/` for v1/v2. A direct
request to `/break` may receive a BusyBox HTTP 404 because there is no file
at that path; it should no longer receive the injected Envoy 503. The
cumulative client 503 counter retains older errors until
the proxy restarts; use fresh requests and the current rate to confirm repair.
If you prefer a single version while investigating, apply `route-stable.yaml`
and expect v1 only, then reapply canary to resume normal learning traffic.

To pause background traffic temporarily, scale only `deployment/lab-client`
to zero; this also removes the interactive client and its metrics target, so
restore it to one before expecting three healthy lab scrapes. Never leave
Prometheus's static target pointing at a removed metrics Service for an
extended period. A full return to unmeshed baseline is an **optional teardown**:
first restore the stable route, scale all three lab Deployments to zero and
wait for their Pods to disappear, then label the lab namespace injection
disabled and Pod Security baseline. Scale the three Deployments to one, verify
new unmeshed Pod IDs and ordinary service responses, delete only the three lab
metrics Services, restore the validated pre-lab Prometheus ConfigMap and
restart only Prometheus. Verify three healthy Restaurant targets and both
alert rules. The dashboard can remain provisioned as historical context.

If any stage fails, stop changes and inspect the lab Pods, events, endpoint
slices, VirtualService, DestinationRule, and `istiod` without mutating other
namespaces. Do not run `istioctl uninstall --purge` as a recovery shortcut.
Delete the lab Namespace only when the exercise is finished and its ownership
has been checked. Control-plane uninstall remains a separate decision.

References: [traffic shifting](https://istio.io/latest/docs/tasks/traffic-management/traffic-shifting/),
[fault injection](https://istio.io/latest/docs/tasks/traffic-management/fault-injection/),
[sidecar injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/),
[Kubernetes native sidecars](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/).
