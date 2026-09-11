# Milestone 032 — Forge YAML Workbench

Started: 2026-09-11

Status: Complete. Source, CI, release publication, hardened deployment, rollout verification, and browser acceptance passed.

## Goal

Provide a small browser-based tool that helps Mike inspect and understand Kubernetes YAML without sending manifests to a backend or granting the application Kubernetes API access.

## Delivered application

Forge YAML Workbench lives under `apps/forge-yaml-workbench` and provides:

- paste, edit, open, format, download, and clear controls
- multi-document YAML parsing
- resource identity, workload, image, Service, probe, resource, volume, and ServiceAccount summaries
- duplicate-key and parser-error reporting
- bounded operational findings for common workload risks
- an expandable object tree
- browser-local processing with no server-side manifest storage

The formatter intentionally produces block-style YAML. Formatting already normalized input is idempotent and may create little visible change.

## Delivery and release engineering

- Dependencies are locked with npm lockfile version 3.
- Node.js 24 runs `npm ci`, six Vitest analyzer tests, the Vite production build, and dependency audit in GitHub Actions.
- A separate guarded workflow builds `linux/amd64` and `linux/arm64` images for pull requests without publishing.
- Only approved version tags publish images; no floating `latest` tag is produced.
- Release `0.1.1` was published by [GitHub Actions run 34650901632](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34650901632).
- Final PR validation passed in Workbench CI run `34651141296`, Kubernetes Manifest Validation run `34651141206`, and multi-architecture Docker run `34651141217`.

Published `0.1.1` OCI index:

```text
wmstipes/signalforge-yaml-workbench:0.1.1
sha256:50e3d115641941bc8f7eaa303463c08ccbafe5842cc07304d4b71dbd4aef8669
```

Platform manifests:

- AMD64: `sha256:f34ad18077137bbf4adea4ba2a354259fe27242f59e52a4f98a0302edc67b1cd`
- ARM64: `sha256:351d010b34a0f65a799b06fd0a59f3c542b5910ece0d45f738bfc0fbc3bc8675`

## Kubernetes design

- Namespace: `forge-tools`
- Deployment: `forge-yaml-workbench`
- Replicas: 1
- Container port: `8080`
- External lab access: NodePort `30081`
- Image: version and OCI index digest pinned
- Namespace Pod Security: restricted, pinned to Kubernetes v1.36
- Pod identity: no RBAC, Kubernetes API access, or mounted ServiceAccount token
- Pod security: non-root, RuntimeDefault seccomp, read-only root filesystem, no privilege escalation, and all Linux capabilities dropped
- Writable storage: bounded 32 MiB `emptyDir` mounted only at `/tmp`
- Probes: startup, readiness, and liveness checks at `/healthz`
- Resources: 25m/250m CPU request/limit and 32Mi/128Mi memory request/limit

## Validation and deployment evidence

Repository validation passed for the Workbench Namespace, Deployment, Service, security context, identity boundary, resources, probes, image, and NodePort.

Before each cluster mutation:

1. Server-side dry-run passed.
2. `kubectl diff` was reviewed.
3. Mike gave separate explicit approval.
4. Only the approved resources were applied.

The initial namespace, Deployment, and Service rollout succeeded. NodePort `30081` returned HTTP 200 for `/healthz` and the application page. The page returned the expected `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and Content Security Policy headers.

The corrected `0.1.1` rollout completed with one available Ready replica and zero restarts. Pod `forge-yaml-workbench-98b546f4d-2bgcj` reported a runtime ImageID matching the pinned OCI index digest.

## Browser defect and regression

The first `0.1.0` browser test found that formatting the two-document sample created an empty Document 2. The YAML library preserved the second document's existing start marker, while the formatter inserted another `---` separator.

The correction clones each parsed document and clears its preserved start marker before joining documents with exactly one separator. A new regression test formats and reparses the sample, requires no adjacent separators or errors, and requires exactly the original Deployment and Service.

Release `0.1.1` passed both browser checks:

- formatting the sample retained two valid documents with no empty document
- formatting flow-style input expanded it into readable block-style YAML while retaining one valid document and its expected operational findings

## Boundaries and limitations

- The Workbench performs YAML parsing and deterministic operational review, not complete Kubernetes OpenAPI schema validation.
- A successful report does not prove API-server admission or runtime success; repository validation and server-side dry-run remain required.
- NodePort `30081` is plain HTTP intended only for the private lab.
- YAML is processed in browser memory and is not sent to or stored by NGINX.
- Formatting already normalized YAML may have no obvious visible effect; a positive status message is a possible future UX improvement.
- Kubernetes API access, RBAC, server-side persistence, Ingress/TLS, and broader policy engines remain outside this milestone.

## Completion gates

- [x] Browser application and bounded analyzer implemented.
- [x] Dependencies locked and install scripts reviewed.
- [x] Unit tests, production build, and audits passed.
- [x] CI and non-publishing multi-architecture image validation passed.
- [x] Versioned image publication explicitly approved and verified.
- [x] Hardened manifests and repository validation added.
- [x] Server-side dry-run and live diff reviewed.
- [x] Cluster mutations separately approved.
- [x] Rollout, health, headers, runtime digest, and browser behavior verified.
- [x] Multi-document formatting defect corrected and regression-tested.
- [x] Architecture, status, roadmap, learning, and milestone documentation reconciled.

Milestone 032 is complete pending final review and explicit merge approval for PR #8.

