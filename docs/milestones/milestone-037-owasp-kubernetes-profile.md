# Milestone 037 — Pinned OWASP Kubernetes Top 10 review profile

Date: 2026-09-13

Status: Immutable `0.5.0` is deployed and runtime-verified. Browser acceptance found a finding-navigation scroll defect; immutable `0.5.1` is published and staged to fix it. Deployment, repeated browser acceptance, PR readiness, and merge remain separate approval gates.

## Goal

Expand Forge YAML Workbench from individual K01 references into an explicit OWASP Kubernetes Top 10:2025 review profile without implying compliance or introducing cluster access.

## Pinned source

- Project: OWASP Kubernetes Top Ten
- Profile: `2025`
- Upstream commit: `828cfa2e2d7af63cdf7025c09ca871265d71f59c`
- Source paths: `2025/en/src/K01-...md` through `K10-...md`
- Finding and profile links use the immutable commit rather than the upstream default branch.

## Coverage contract

| Category | Label | What the Workbench can establish from the current editor input |
| --- | --- | --- |
| K01 Insecure Workload Configurations | Direct | Bounded workload security settings already covered by deterministic findings |
| K02 Overly Permissive Authorization Configurations | Partial | RBAC wildcards, escalation verbs, nodes/proxy, Secret reads, and cluster-admin bindings present in the file |
| K03 Secrets Management Failures | Partial | Secret environment injection and literal cloud credential environment variables present in the file |
| K04 Lack of Cluster-Level Policy Enforcement | Partial | Namespace Pod Security Admission labels and supplied admission-policy resources |
| K05 Missing Network Segmentation Controls | Partial | Supplied NetworkPolicy resources |
| K06 Overly Exposed Kubernetes Components | Partial | NodePort, LoadBalancer, and Ingress declarations |
| K07 Misconfigured and Vulnerable Cluster Components | Cluster context required | No manifest-only validity claim; live component configuration and vulnerability state are required |
| K08 Cluster-to-Cloud Lateral Movement | Partial | Literal cloud credential environment variables present in supplied workloads |
| K09 Broken Authentication Mechanisms | Partial | Automatic ServiceAccount-token mounting in supplied workloads |
| K10 Inadequate Logging and Monitoring | Cluster context required | No manifest-only validity claim; audit, logs, alerts, retention, and monitoring health require runtime context |

`Direct` means the bounded settings named above are directly represented in the YAML. `Partial` means only listed manifest-local signals are reviewed. `Cluster context required` means the Workbench does not attempt an answer. None of the labels is a score, compliance result, or category pass.

## Implementation

- Added a ten-category profile rendered after the existing syntax, operational, and Kubernetes-schema sections.
- Kept finding severity independent from OWASP coverage labels.
- Added shared mappings where one finding informs multiple categories, including K01/K09 for automatic ServiceAccount tokens and K03/K08 for literal cloud credentials.
- Added actionable, clickable deterministic findings for bounded RBAC, secret delivery, Namespace policy labels, and exposure declarations.
- Counts only manifest-local signals and explicitly states that zero matching signals is not a pass result.
- Preserved unsupported schema and unavailable CRD states independently of the OWASP profile.

## Trust and safety boundary

- YAML remains in browser memory.
- No backend, Kubernetes credentials, API calls, RBAC, runtime schema fetches, cloud access, or policy-engine calls are added.
- Secret values are never displayed in findings or sent elsewhere; checks use field shape and selected environment-variable names.
- No remediation is applied automatically. Copyable examples still require operator review.
- Effective RBAC, admission, network, exposure, component, authentication, cloud, audit, logging, and monitoring state remain outside the Workbench.
- General YAML mode produces no Kubernetes schema, operational, remediation, or OWASP profile output.

## Local verification

- 50 tests pass across analyzer, schema, OWASP profile, and browser-rendered behavior, including finding-link scrolling in a long manifest.
- All ten category IDs, labels, immutable source links, non-score language, multi-category mappings, and General YAML suppression are covered.
- Production build passed at 706.33 kB JavaScript / 110.42 kB gzip.
- Validator reproducibility passed for all 12 bundled Kubernetes schemas.
- The production CSP scan found no `eval` or Function-constructor usage.
- Dependency audit reports zero vulnerabilities.
- Repository Kubernetes-manifest validation and whitespace checks pass.
- Draft PR #14 is published; Workbench CI, Kubernetes manifest validation, and the non-publishing multi-architecture build pass.
- Separately approved publication run `34787257312` produced OCI index `sha256:11e8fcc4989fe7dcdc1c5312786b80189a98b6a9acb82e979aa8235d756fcb8e`.
- Active platform manifests are AMD64 `sha256:2a47101b9f176671e0954ca55e90b7ae4dfe42ba4b7ce5856ccd2f447822032e` and ARM64 `sha256:f1de89162f2de896d8907e2fcce17d511246881c919fa15e6ee3a1ea3f6077b3`.
- The immutable `0.5.0` index is deployed. Its Pod is Ready with zero restarts, the runtime ImageID matches, the EndpointSlice has one ready address, health and page requests return HTTP 200, and strict security headers remain present.
- Live browser acceptance confirmed the OWASP profile and General YAML isolation, then found that finding controls selected the correct line without scrolling it into view.
- Source `0.5.1` explicitly scrolls the editor to center the selected line and preserves the selected text.
- Separately approved publication run `34789023192` produced OCI index `sha256:4011478de37f9316d65985f17d87d3652203e2bcffd75ee29646ddcd52a64ffa`.
- Active patch platform manifests are AMD64 `sha256:ebad025531960fa9d18a67fd153aa4fd2c56556df87574f06db083564981d5d5` and ARM64 `sha256:bfabd7f46865db81a8d8b57954dc4c0c2ddcb01a7705390b3e633b6acb2e8238`.
- The tracked Deployment stages the immutable `0.5.1` index without applying it.

## Remaining gates

1. Review server-side dry-run and live diff before any separately approved Deployment update.
2. Repeat live browser acceptance against the corrected immutable image.
3. Keep PR readiness and merge separately approved.
