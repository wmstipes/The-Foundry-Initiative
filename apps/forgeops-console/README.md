# ForgeOps Console

ForgeOps Console C4 is a local, browser-based, read-only Kubernetes resource
viewer. Its Go core owns explicit kubeconfig handling, typed client access,
scope generations, strict resource projections, limits, and the compiled
first-party plugin broker. The browser receives no raw Kubernetes objects or
credentials from kubeconfig. Application-authored logs and Events can themselves
contain sensitive data; they are not guaranteed redacted.

## C4 boundary

- one explicit regular kubeconfig file is required;
- the listener must be a literal loopback address;
- parsed context metadata is sanitized before it reaches the browser;
- context, namespace, generation, activity, and the session nonce remain in
  memory;
- the compiled `forge.resources` plugin can list or read only Namespaces,
  Nodes, Deployments, ReplicaSets, Pods, Services, and EndpointSlices;
- responses are fixed projections bounded to 200 objects and 1 MiB;
- resource requests have a five-second timeout and a four-request concurrency cap;
- the compiled `forge.diagnostics` plugin adds bounded selected-Pod logs and
  Events, plus offline explanatory command previews; and
- there are no Secrets, ConfigMap values, watches, mutations,
  exec, attach, proxy, port-forward, dynamic plugins, persistence, packaging,
  images, or deployments.

The production client accepts only embedded kubeconfig material and rejects
exec plugins, auth-provider plugins, secondary credential files, proxies,
insecure TLS, and impersonation. A separate synthetic-demo entry point uses a
fake client and never loads kubeconfig.

## Changing contexts

The context dropdown lists contexts from the single explicit `--kubeconfig`
file loaded when the core starts. Choose a context, click **Activate**, then
choose a namespace and click **Set scope**. Activation resets the namespace,
clears current resource/diagnostic selections, and creates a new generation.
It does not change the kubeconfig's `current-context`.

To add contexts, update that file using your usual trusted configuration
workflow, then stop and restart Console with the same explicit file. To use a
different file, restart with that file's `--kubeconfig` path. Browser refresh
alone does not reload the file. Console does not merge ambient KUBECONFIG
paths, discover other files, or offer browser-side credential upload.

Context discovery does not establish authentication support or access. Standard
EKS kubeconfigs use executable AWS credential retrieval (`aws eks get-token`);
the current production client rejects exec credential plugins, so such a
context may appear but its cluster reads fail. Do not remove this restriction
or copy temporary tokens into files as a suggested workaround. Cloud
authentication needs an explicit reviewed design. See
[AWS EKS kubeconfig documentation](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html)
and the [C6 planning proposal](../../../docs/milestones/forgeops-console-c6-plugin-compatibility-planning.md).

## Pod diagnostics

Select a Pod, review the sensitive-data warning, then explicitly select a
container before reading logs. Current or previous container-instance logs are
snapshots: no follow, automatic refresh, download, or persistent history.
Events are filtered to the current selected Pod UID and projected as text.
The UI offers regular containers; the core also validates init-container names.

Diagnostic limits: five seconds, two simultaneous requests (separate from the
four resource slots), 64 KiB / 500 log lines, 100 Events, 1024 bytes per Event
message, and 256 KiB encoded JSON. Limits and API pagination mark incomplete
results; timeout/disconnection discards partial content. Unsafe terminal and
Unicode formatting controls are replaced. Content remains untrusted plain text.
Only capability/scope/outcome/count metadata enters the bounded activity list.

Cancel, change Pod, or change scope to abort and clear diagnostics. Late results
are rejected using request identity and generation. Scope selection checks the
generation atomically. Logs cannot be UID-preconditioned by the Kubernetes log
endpoint, so Pod recreation between validation and log reading remains a limit.

Command previews are labeled **not executed**, quoted separately for PowerShell
and POSIX shells, and include a manual kubeconfig placeholder. They are related
commands, not exact equivalents of the Console's projection, generation, and
limit behavior. Preview generation does not contact Kubernetes or prove access.

## Local developer validation

Requirements are Go 1.27 and Node.js 24.

```text
cd apps/forgeops-console
go test ./...
go vet ./...

cd web
npm ci
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

After building the browser, start the progress demo with:

```text
go run ./cmd/forgeops-console-demo \
  --web-dir ./web/dist \
  --listen 127.0.0.1:9090
```

Open `http://127.0.0.1:9090`, activate `synthetic-demo`, choose the
`signalforge` namespace, and select a resource. The permanent synthetic banner
and separate binary make clear that no cluster connection exists.

The production entry point is `./cmd/forgeops-console` and requires an explicit
`--kubeconfig`. Do not use it for a live check until that separately approved
C4 live acceptance step is authorized. The earlier C3 read-only walkthrough
does not authorize log or Event disclosure.
