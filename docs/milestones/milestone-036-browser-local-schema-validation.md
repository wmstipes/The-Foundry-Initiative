# Milestone 036 — Browser-local Kubernetes schema validation

Started: 2026-09-13

Status: The separately approved `0.4.0` image was deployed and passed workload, digest, endpoint, health, page, and security-header checks. Live browser acceptance found a blank-page defect because runtime AJV compilation was blocked by the strict Content Security Policy. The `0.4.1` source and AMD64/ARM64 image are published, and its immutable Deployment update is staged for review; deployment, repeated live browser acceptance, PR readiness, and merge remain separate approval gates.

## Goal

Add bounded Kubernetes schema validation against one explicitly pinned Kubernetes version while preserving the Workbench's browser-only trust boundary and the existing separation between Kubernetes and General YAML inspection.

## Bounded scope

- Keep Kubernetes as the startup default.
- Pin schema validation to Kubernetes `v1.36.4`, matching the SignalForge control plane at milestone start.
- Bundle schema data with the static application and run validation in browser memory.
- Present YAML syntax, Kubernetes document-shape errors, deterministic operational findings, and schema results in separate sections.
- Support an explicit initial set of 12 stable resource GVKs.
- Report other built-in resources as unsupported.
- Report external API-group resources as `CRD schema unavailable`.
- Preserve General YAML as syntax and structure inspection without Kubernetes operational or schema findings.

## Supported resource schemas

| API version | Supported kinds |
| --- | --- |
| `v1` | `ConfigMap`, `Namespace`, `Pod`, `Secret`, `Service`, `ServiceAccount` |
| `apps/v1` | `DaemonSet`, `Deployment`, `ReplicaSet`, `StatefulSet` |
| `batch/v1` | `CronJob`, `Job` |

Support is an exact `apiVersion` and `kind` match. A built-in GVK outside this table is neither schema-valid nor schema-invalid; it is unsupported by this bundle. A resource in an external API group is neither schema-valid nor schema-invalid; its CRD schema is unavailable.

## Schema provenance and reproducibility

- Kubernetes version: `v1.36.4`
- Upstream file: [`api/openapi-spec/swagger.json`](https://github.com/kubernetes/kubernetes/blob/v1.36.4/api/openapi-spec/swagger.json)
- Upstream SHA-256: `dcede2063da1d7ad62ecb5af8adb6d7fabd0b52385a7fa0048afb491dac90450`
- Generated browser bundle: `apps/forge-yaml-workbench/src/schema/kubernetes-v1.36.4.json`
- Bundle contents: 12 resource mappings and 196 transitive definitions
- Validator generator: exactly pinned `ajv@8.20.0`

The checked-in generator rejects any input file whose checksum differs from the pinned upstream source. It also normalizes Kubernetes `IntOrString` fields and closes documented object-property sets so wrong types and unknown fields are reported locally.

AJV emits the 12 standalone validator functions during development. The generated module is checked in and reproducibility-checked before each production build, so the browser does not use dynamic JavaScript evaluation. CI scans the final JavaScript assets and rejects `eval` or `new Function`, preserving the strict production Content Security Policy.

## Result contract

Schema results use five explicit states:

| State | Meaning |
| --- | --- |
| `valid` | The resource matches its bundled `v1.36.4` schema. |
| `invalid` | One or more field paths do not match the bundled schema. |
| `unsupported` | The GVK is built-in but is outside the explicit support set. |
| `schema-unavailable` | The API group is external and no CRD schema is bundled. |
| `not-evaluated` | `apiVersion` or `kind` is missing, so no schema can be selected. |

Schema mismatches include a YAML path and navigate to the nearest source location. Unsupported, unavailable, and not-evaluated resources are never counted as valid or invalid.

## Guardrails

- YAML remains in browser memory and is not sent to a backend.
- Schema data ships as static application content; validation performs no runtime fetch.
- The Workbench has no ServiceAccount token, RBAC, Kubernetes API access, or cluster credentials.
- Schema validation is not API-server admission, defaulting, conversion, policy evaluation, webhook evaluation, discovery, or server-side dry-run.
- CRD schemas are not inferred from or applied from YAML in the editor.
- No new OWASP rules are included; broader OWASP Kubernetes Top 10:2025 coverage remains Milestone 037.
- No image publication, manifest update, deployment, live browser acceptance, or merge occurs without its separate approval checkpoint.

## Local verification evidence

- [x] Clean baseline confirmed at `main` commit `55fc08ac1098c1ed48bf98b9e67f5d3df9fb55da`.
- [x] Generated bundle checksum, resource count, and transitive definition count verified.
- [x] Analyzer and schema tests cover valid, invalid, unsupported, unavailable-CRD, not-evaluated, unknown-field, wrong-type, `IntOrString`, and source-location behavior.
- [x] DOM tests cover separate report sections and explicit unsupported/unavailable labels.
- [x] General YAML tests prove Kubernetes operational and schema results remain absent.
- [x] All 42 tests pass, including loading and exercising every precompiled schema in the explicit support set.
- [x] The local `0.4.1` production build passes; output JavaScript is 695.62 kB uncompressed and 106.88 kB gzip.
- [x] Validator generation is reproducible and the production bundle contains no `eval` or `new Function` usage.
- [x] Dependency audit reports zero vulnerabilities.
- [x] Whitespace validation passes.
- [x] Branch publication is approved and complete through draft PR #13.
- [x] Pull-request CI and non-publishing multi-architecture image build pass in runs `34778172043` and `34778172060`.
- [x] Versioned `0.4.0` image publication is separately approved and passed in run `34778468753`; the AMD64/ARM64 OCI index digest is `sha256:96e3d8e4a1b563d5d719521bbd8f0d5f6f3e3a5fc3a299851d21186a20de3477`.
- [x] The Deployment manifest and validator pin the reviewed `0.4.0` OCI index without changing namespace, Service, replicas, probes, resources, security context, or volumes.
- [x] The `0.4.0` Deployment diff was separately reviewed and approved before cluster mutation.
- [x] The `0.4.0` rollout, runtime digest, ready EndpointSlice, health endpoint, page response, CSP, and `nosniff` checks passed.
- [x] Live browser acceptance found and documented the strict-CSP startup defect; it did not accept `0.4.0`.
- [x] The reviewed `0.4.1` source correction is published on draft PR #13.
- [x] The separately approved `0.4.1` image publication passed in run `34780773917`; the active AMD64/ARM64 OCI index digest is `sha256:96c715c938f1636686190e294829c61f0f7af71117b353bd2df05a9fc67bddf2`.
- [x] The Deployment manifest and validator stage the immutable `0.4.1` index without changing namespace, Service, replicas, probes, resources, security context, or volumes.
- [ ] Review server-side dry-run and live diff, then separately approve the replacement deployment.
- [ ] Repeat live browser acceptance after the corrected deployment.
- [ ] Final merge is separately approved and complete.

## Deferred

- Additional built-in GVK schemas remain later, explicit support-set increments.
- Runtime CRD discovery, user-supplied CRD schema registration, and applying CRDs from the editor remain out of scope.
- API-server discovery, admission requests, policy-engine integration, automatic YAML mutation, and server-side persistence remain out of scope.
- Broader OWASP Kubernetes Top 10:2025 coverage remains Milestone 037.
