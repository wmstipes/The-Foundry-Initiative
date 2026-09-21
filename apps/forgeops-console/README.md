# ForgeOps Console

ForgeOps Console C3 is a local, browser-based, read-only Kubernetes resource
viewer. Its Go core owns explicit kubeconfig handling, typed client access,
scope generations, strict resource projections, limits, and the compiled
first-party plugin broker. The browser receives no raw Kubernetes objects or
credentials.

## C3 boundary

- one explicit regular kubeconfig file is required;
- the listener must be a literal loopback address;
- parsed context metadata is sanitized before it reaches the browser;
- context, namespace, generation, activity, and the session nonce remain in
  memory;
- the compiled `forge.resources` plugin can list or read only Namespaces,
  Nodes, Deployments, ReplicaSets, Pods, Services, and EndpointSlices;
- responses are fixed projections bounded to 200 objects and 1 MiB;
- requests have a five-second timeout and a four-request concurrency cap; and
- there are no Secrets, ConfigMap values, Events, logs, watches, mutations,
  exec, attach, proxy, port-forward, dynamic plugins, persistence, packaging,
  images, or deployments.

The production client accepts only embedded kubeconfig material and rejects
exec plugins, auth-provider plugins, secondary credential files, proxies,
insecure TLS, and impersonation. A separate synthetic-demo entry point uses a
fake client and never loads kubeconfig.

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
C3 acceptance step is authorized.
