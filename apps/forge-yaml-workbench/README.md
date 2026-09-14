# Forge YAML Workbench

Forge YAML Workbench is a browser-based YAML inspector for the SignalForge lab. It parses YAML locally in the browser and offers Kubernetes-specific and General YAML inspection modes.

## Version 0.6.0 candidate source scope

- Paste, edit, open, format, and download YAML.
- Parse multi-document YAML files.
- Start in Kubernetes mode and explicitly switch to General YAML mode without changing the editor contents.
- Accept mapping, sequence, and scalar document roots in General YAML mode.
- Summarize each General YAML document by root type and shape while suppressing Kubernetes-only operational findings.
- Display resource identity, namespace, labels, selectors, replicas, Services, containers, images, tags or digests, ports, probes, resources, volumes, and ServiceAccount use.
- Show an expandable object tree.
- Detect YAML parser errors and duplicate keys.
- Validate an explicit set of Kubernetes resources against a browser-local schema bundle pinned to Kubernetes `v1.36.4`.
- Present YAML syntax, deterministic operational findings, and schema-validation results as separate report sections.
- Report unsupported built-in resources, unavailable CRD schemas, and incomplete resource identities without calling them valid or invalid.
- Surface bounded operational findings such as mutable image tags, missing probes or resources, privileged containers, root execution, HostPath use, and automatic ServiceAccount-token mounting.
- Present a pinned OWASP Kubernetes Top 10:2025 review profile with direct, partial, and cluster-context-required labels.
- Center the editor on a finding's selected line when its YAML path or line/column control is activated.
- Perform analysis in the browser without sending YAML to another service.

## Milestone 033 usability improvements

The `0.1.2` release keeps the same browser-local trust boundary while improving interaction precision:

- explicit feedback when formatting changes YAML or the input is already normalized
- parser diagnostics with clickable line and column locations
- preservation of an opened YAML filename when downloading
- keyboard shortcuts for opening, formatting, and downloading
- confirmation before clearing unsaved edits
- DOM interaction coverage alongside the analyzer tests

## Milestone 034 deterministic checks

The `0.2.0` release deepened the bounded operational review with:

- clickable YAML paths, plain-language explanations, and suggested corrections for every operational finding
- workload selector and Pod-template label consistency checks
- duplicate resource identity detection across multi-document input
- Service selector and named target-port checks against workloads included in the same file
- host PID and IPC namespace findings
- explicit container checks for privilege escalation, writable root filesystems, Linux capabilities, and non-root execution
- expandable fix guidance with copyable YAML examples and operational cautions
- initial OWASP Kubernetes Top 10:2025 K01 mapping, including an explicit RuntimeDefault seccomp check
- parsed-document and finding counts that avoid implying API-server validity

These checks are deterministic and browser-local. They do not replace Kubernetes OpenAPI validation, admission control, or server-side dry-run.

The OWASP references identify which security guidance informed a finding; they are not a claim that the Workbench performs a complete OWASP compliance assessment. Broader OWASP Kubernetes Top 10:2025 coverage is planned as a separate milestone.

## Milestone 036 schema validation

The checked-in schema bundle is derived from Kubernetes `v1.36.4` [`api/openapi-spec/swagger.json`](https://github.com/kubernetes/kubernetes/blob/v1.36.4/api/openapi-spec/swagger.json). The generator accepts only the pinned upstream file with SHA-256 `dcede2063da1d7ad62ecb5af8adb6d7fabd0b52385a7fa0048afb491dac90450` and retains the transitive definitions needed by this explicit support set:

| API version | Supported kinds |
| --- | --- |
| `v1` | `ConfigMap`, `Namespace`, `Pod`, `Secret`, `Service`, `ServiceAccount` |
| `apps/v1` | `DaemonSet`, `Deployment`, `ReplicaSet`, `StatefulSet` |
| `batch/v1` | `CronJob`, `Job` |

An exact GVK outside this table is reported as unsupported when it belongs to a Kubernetes API group. A resource in an external API group is reported as having an unavailable CRD schema. The Workbench does not infer or retrieve CRD schemas, including CRDs present in the same YAML file.

To reproduce the generated bundle from an independently downloaded pinned source file:

~~~powershell
npm.cmd run schema:build -- C:\path\to\kubernetes-v1.36.4-swagger.json
~~~

The generator rejects a file whose SHA-256 does not match the pinned source.

The checked-in validators are precompiled during development and verified again by the production build. The browser does not compile schemas dynamically, so validation remains compatible with the production Content Security Policy without allowing `unsafe-eval`.

## Validation boundary

The Workbench performs YAML parsing in both modes. Kubernetes mode adds deterministic operational checks and bounded schema validation for the supported table above; General YAML mode does not infer Kubernetes semantics or produce schema results. All parsing, operational checks, bundled schema lookup, and validation run in browser memory.

The schema result is not API-server admission validation. The Workbench does not contact a cluster, evaluate admission webhooks or policies, apply API defaulting or conversion, discover installed API resources, or retrieve CRD schemas. A schema-valid result therefore does not prove that a manifest will be admitted or run successfully.

## Milestone 037 OWASP review profile

The profile is pinned to OWASP source commit `828cfa2e2d7af63cdf7025c09ca871265d71f59c`. Coverage labels describe the Workbench's observation boundary, not a compliance score or pass/fail result.

| Category | Coverage | Browser-local scope |
| --- | --- | --- |
| K01 Insecure Workload Configurations | Direct | Workload security contexts, host namespaces, HostPath, resources, and ServiceAccount-token settings |
| K02 Overly Permissive Authorization Configurations | Partial | Supplied RBAC rules, wildcards, escalation verbs, nodes/proxy, Secret reads, and cluster-admin bindings |
| K03 Secrets Management Failures | Partial | Supplied Secret environment injection and literal cloud credential environment variables |
| K04 Lack of Cluster-Level Policy Enforcement | Partial | Supplied Namespace Pod Security Admission labels and policy resources |
| K05 Missing Network Segmentation Controls | Partial | Presence of supplied NetworkPolicy resources |
| K06 Overly Exposed Kubernetes Components | Partial | Supplied NodePort, LoadBalancer, and Ingress declarations |
| K07 Misconfigured and Vulnerable Cluster Components | Cluster context required | Component configuration, versions, patches, and runtime vulnerabilities |
| K08 Cluster-to-Cloud Lateral Movement | Partial | Literal cloud credential environment variables in supplied workloads |
| K09 Broken Authentication Mechanisms | Partial | Automatic ServiceAccount-token mounting in supplied workloads |
| K10 Inadequate Logging and Monitoring | Cluster context required | Audit, log, alert, retention, and monitoring state |

Partial coverage never establishes that the category passed. Effective RBAC, admission, segmentation, exposure, identity, component, cloud, audit, logging, and monitoring state require context the Workbench deliberately does not access.

Before deployment, continue to use repository validation and Kubernetes server-side dry-run.

## Milestone 038 formatting preview

The `0.6.0` candidate changes formatting from immediate editor mutation into an explicit review workflow:

- valid YAML with formatting changes opens a browser-local, line-oriented preview
- before and after line numbers accompany added, removed, and unchanged lines
- the editor remains unchanged until **Apply formatting** is selected
- **Cancel** and Escape preserve the original YAML
- keyboard focus starts inside the preview, remains contained, and returns to the Format control
- final-newline and line-ending normalization are labeled explicitly
- unusually large comparisons use a bounded, labeled simplified alignment
- invalid YAML continues to remain unchanged and routes to the Validation report

The preview reuses the existing deterministic formatter. It does not repair invalid YAML, infer intended indentation, or provide automatic remediation.

## Local development

Use the committed lockfile for reproducible installation:

~~~powershell
npm.cmd ci
npm.cmd run validators:check
npm.cmd test
npm.cmd run build
npm.cmd run csp:check
~~~

## Container

The production container uses the committed lockfile to compile the static application and serves it on port `8080` with an unprivileged NGINX runtime.
