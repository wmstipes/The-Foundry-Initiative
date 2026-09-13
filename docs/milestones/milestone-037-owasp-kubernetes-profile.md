# Milestone 037 — Pinned OWASP Kubernetes Top 10 review profile

Date: 2026-09-13

Status: Implemented and verified locally. Branch publication, image publication, deployment, live browser acceptance, PR readiness, and merge remain separate approval gates.

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

- 49 tests pass across analyzer, schema, OWASP profile, and browser-rendered behavior.
- All ten category IDs, labels, immutable source links, non-score language, multi-category mappings, and General YAML suppression are covered.
- Production build passed at 706.33 kB JavaScript / 110.42 kB gzip.
- Validator reproducibility passed for all 12 bundled Kubernetes schemas.
- The production CSP scan found no `eval` or Function-constructor usage.
- Dependency audit reports zero vulnerabilities.
- Repository Kubernetes-manifest validation and whitespace checks pass.

## Remaining gates

1. Obtain approval before publishing the branch or creating/updating a pull request.
2. Keep image publication separately approved.
3. Review server-side dry-run and live diff before any separately approved Deployment update.
4. Repeat live browser acceptance against the deployed immutable image.
5. Keep PR readiness and merge separately approved.
