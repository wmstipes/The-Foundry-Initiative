# ForgeOps Console

ForgeOps Console C2 is an offline walking skeleton for the planned local,
browser-based Kubernetes inspection tool. It proves the loopback HTTP boundary,
explicit kubeconfig parsing, in-memory context selection, compiled first-party
plugin registration, and deny-by-default capability broker without contacting a
cluster.

## C2 boundary

- one explicit regular kubeconfig file is required;
- the listener must be a literal loopback address;
- parsed context metadata is sanitized before it reaches the browser;
- context selection and the session nonce remain in memory;
- only the compiled `forge.example` plugin is registered;
- the example capability returns a fixed offline status;
- there are no Kubernetes reads, mutations, streams, logs, exec operations,
  dynamic plugins, persistence, packaging, images, or deployments.

The `internal/cluster.OfflineFactory` seam deliberately refuses to construct a
Kubernetes client. Replacing it requires the separately approved C3 boundary.

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

After building the browser shell, the fixture-only application can be started
locally with:

```text
go run ./cmd/forgeops-console \
  --kubeconfig ./fixtures/kubeconfig.yaml \
  --web-dir ./web/dist \
  --listen 127.0.0.1:9090
```

Opening `http://127.0.0.1:9090` displays the shell. Selecting the fixture
context changes only local in-memory state; it does not use the fixture server
address or token.
