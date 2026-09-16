# Learning Journal

Use this journal to capture progress without requiring polished prose.

## Entry template

### Date

### What I worked on

### What I learned

### What was difficult

### What I finished

### Next small step

---

## 2026-07-18

### What I worked on

Created the initial structure and guiding documents for The Foundry Initiative.

### What I learned

A project can begin with structure and intent before its first technical implementation is selected.

### What was difficult

Starting something meaningful can create pressure to make it large or perfect immediately.

### What I finished

Established a repository scaffold, roadmap, project vision, contribution workflow, and architecture placeholder.

### Next small step

Choose a first artifact that can be completed and demonstrated in a short development cycle.

---

## 2026-09-08

### What I worked on

Built SignalForge from an initial Raspberry Pi Kubernetes lab into a repeatable application and observability platform. The work progressed through Milestones 001-023 and culminated in Restaurant API `0.7.0` with lightweight Prometheus collection.

### What I learned

- Small milestones make a multi-component platform easier to build, test, and explain.
- A Kubernetes Service is useful for stable application access, but Prometheus should discover and scrape each replica directly when per-Pod counters matter.
- Application metrics and the Kubernetes Metrics API solve different problems; installing Prometheus does not make `kubectl top` available.
- Histogram buckets can be aggregated across replicas, making them appropriate for fleet-wide latency percentiles.
- Metric labels need the same design discipline as an API. Route templates and a bounded `unmatched` value prevent uncontrolled cardinality.
- Automated tests, manifest validation, pinned images, and operator helpers turn successful commands into a repeatable engineering workflow.
- Cross-platform quoting deserves explicit testing when PowerShell launches commands inside Linux containers.

### What was difficult

The most subtle problem was distinguishing a healthy metrics collector from broader cluster resource monitoring. Another challenge was correcting the Prometheus target-check helper after nested PowerShell and shell quoting produced an unterminated-string failure.

Release sequencing also required care: application changes, GitHub Actions, a version tag, the ARM64 image build, Kubernetes deployment, smoke tests, and Prometheus validation each had to complete in the right order.

### What I finished

- Deployed and operated a four-node Kubernetes cluster.
- Released Restaurant API `0.7.0` as three healthy replicas.
- Added application CI, ARM64 image publishing, versioned Kubernetes manifests, and validation automation.
- Added laptop-based deployment, smoke-test, status, log, and metrics helpers.
- Created and exercised an operator runbook.
- Deployed a least-privilege Prometheus collector with three healthy Pod targets.
- Added request latency, application-versus-synthetic traffic classification, and label-cardinality protection.
- Verified the live application, automatic target discovery, and baseline PromQL queries.

### Next small step

Select Milestone 024. Evaluate whether Kubernetes Metrics Server provides enough operational value to justify its footprint in the Raspberry Pi cluster.

---

## 2026-09-08 - Milestone 024

### What I worked on

Evaluated Kubernetes Metrics Server for SignalForge, repaired the cluster's kubelet serving-certificate configuration, and enabled current node and Pod resource visibility.

### What I learned

- Prometheus application metrics and the Kubernetes resource Metrics API are complementary rather than interchangeable.
- A healthy kubelet can still present a serving certificate that is unsuitable for a secure metrics client.
- `rotateCertificates: true` controls kubelet client-certificate rotation; `serverTLSBootstrap: true` is separately required for signed serving certificates.
- Core Kubernetes does not automatically approve kubelet serving CSRs because an operator must confirm that the requested DNS names and IP addresses belong to the requesting node.
- A TLS-authenticated request can correctly return HTTP 401. That response proves the certificate and connection succeeded while unauthenticated application access was rejected.
- `kubectl top` is useful for immediate operational checks, while historical analysis still belongs in Prometheus.

### What was difficult

The initial failure appeared to be a Metrics Server installation problem, but testing exposed three underlying identity issues: Windows SSH used the wrong username, the cluster nodes lacked durable hostname mappings, and kubelets served self-signed certificates containing only DNS SANs. Repairing the trust chain required verified SSH host keys, one-node-at-a-time kubelet changes, and manual inspection of every serving CSR.

### What I finished

- Restored verified, passwordless administrative SSH from `forge-head` to all workers.
- Made the SignalForge hostname mappings durable against cloud-init regeneration.
- Enabled kubelet serving-certificate bootstrap locally and in the kubeadm ConfigMap.
- Reviewed and approved four node-specific `kubernetes.io/kubelet-serving` CSRs.
- Verified Kubernetes-CA trust and InternalIP SANs on every kubelet endpoint.
- Deployed pinned Metrics Server v0.9.0 without `--kubelet-insecure-tls`.
- Enabled `kubectl top nodes` and `kubectl top pods` for all four nodes.
- Measured Metrics Server at 4m CPU and 21 MiB memory and retained it.

### Next small step

Plan persistent NVMe-backed Prometheus storage before replacing the intentionally ephemeral `emptyDir` volume.

---

## 2026-09-09 - Milestone 025

### What I worked on

Compared practical persistent-storage designs for the SignalForge Prometheus server and converted the result into an explicit implementation and recovery plan before touching the NVMe or live cluster.

### What I learned

- Persistence and high availability are separate properties. A local PV preserves data across Pod replacement but cannot follow the workload to another node.
- PV node affinity lets the Kubernetes scheduler understand a local disk's physical location; a plain `hostPath` does not express that relationship as safely in a multi-node cluster.
- Prometheus's TSDB favors a local POSIX filesystem and does not support NFS, even when network storage initially appears more flexible.
- A retention-size limit needs free space for the WAL, head chunks, and compaction. The application limit should stay below the filesystem's full capacity.
- A missing-mount safeguard matters as much as the normal mount path. Otherwise, a valid directory can silently redirect heavy writes back to the SD card.
- Backups must leave the storage node and be restore-tested; `Retain` protects data from Kubernetes deletion behavior but is not a backup.

### What was difficult

The main tradeoff was accepting that the lightest design is intentionally node-bound. Adding NFS or a distributed storage platform would appear to improve mobility, but it would either conflict with Prometheus storage guidance or add more operational burden than this single workload justifies.

It also required keeping the planning milestone distinct from implementation. The approved design is now documented, but the repository still truthfully describes the live collector as ephemeral.

### What I finished

- Selected a static `local` PV on a dedicated ext4 partition of the `forge-head` NVMe.
- Defined capacity, retention, StorageClass, reclaim, affinity, and workload-strategy decisions.
- Documented Pod, node, NVMe, deletion, and missing-mount failure behavior.
- Defined weekly off-node cold backups, recovery objectives, restore validation, migration, and rollback.
- Created a strict pre-deployment acceptance gate for Milestone 026.
- Made no live cluster or storage changes.

### Next small step

Implement Milestone 026 by verifying the NVMe identity first, then creating and validating the partition, mount, static storage resources, Prometheus cutover, backup, and rollback path.


## 2026-09-10 - Milestone 026

Completed the NVMe-backed Prometheus cutover, Pod-replacement persistence test, off-node cold backup, isolated restore analysis, port-forward check, and rollback/return drill. The installed disk was a Samsung 950 PRO 512GB rather than the originally planned 2 TB device; inventory and destructive-testing gates caught that discrepancy before deployment.

Lessons: a metric exposed by Prometheus is not automatically stored in its query database; readiness must read `/metrics` when self-scraping is absent. Windows PowerShell nested-shell quoting broke a restore check, so direct command arguments replaced it. A try/finally recovery path restored persistent collection even when execution policy blocked a test script. Use the established process-scoped execution-policy invocation for operator helpers.

Recovery evidence must stay precise: six blocks were listed and the newest analyzed, but full service recovery and the one-hour RTO were not measured. Weekly backups remain manual. The temporary rollback Pod became Ready; its target check was blocked, while the restored persistent collector passed all three-target checks and loaded six retained blocks.

Next small step: plan lightweight Grafana and dashboard requirements for proposed Milestone 027.

## 2026-09-10 - Milestone 030 offline preparation

Milestone 029 was accepted and merged at `1837868`. The next increment translates its two scrape-coverage conditions into unactivated rules and synthetic test cases.

Engineering notes: alert identity belongs in stable labels; changing diagnostic counts belong in annotations. Failed scrapes, missing discovery series, and stopped evaluation are different situations. A transition between warning and critical conditions starts the other rule's independent delay, so an explicit pending-only interval is part of the accepted design. The critical expression's absent branch does not return a healthy-target count and must not be described as one.

Source-level tests and inactive-configuration guards passed, but they do not prove PromQL behavior. The preparation environment lacked promtool and Docker; subsequent [GitHub Actions run 34542077003](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34542077003) supplied the missing evidence for commit `29a6e31`: real promtool 3.13.2 validated both rules and passed all 19 scenarios. PR #5 later merged at `604e38e`. Offline correctness does not establish operational delay suitability or authorize activation.

## 2026-09-10 - Milestone 030 activation review preparation

The activation candidate reuses the ConfigMap already mounted at `/etc/prometheus`: one embedded canonical rule file and one exact `rule_files` entry are sufficient, with no Deployment, RBAC, storage, Grafana or receiver change.

The safety boundary belongs in the operator path as well as the manifest. The helper therefore defaults to inspection, classifies the live ConfigMap by normalized hashes, requires the known context/image/replica/target baseline, shows recent coverage history and `kubectl diff`, and stops before mutation. Explicit activation first writes a validated recovery object; failed post-change verification triggers rollback. Repository desired state, evaluator-visible firing state and delivered notification are three different claims and must remain separate.

Next small step: review the repository diff and read-only live plan. Only a separate operator decision can authorize activation.

## 2026-09-11 - Milestone 030 guarded activation

The read-only plan found the exact baseline, three healthy targets, no loaded rules, and no below-three samples across 24 hours. Its first two attempts exposed a Windows-specific detail: `kubectl diff` needs an external `diff.exe`, while Windows PowerShell defines `diff` as an alias for `Compare-Object`. Restricting detection to an application and locating Git for Windows' bundled executable made the review portable without changing the cluster.

After PR #6 merged and Mike explicitly approved activation, the helper saved and verified the baseline ConfigMap, applied only the accepted ConfigMap, restarted only Prometheus, and completed all post-change checks. An independent plan then found no repository/live diff and reconfirmed three healthy targets with both rules healthy and inactive. The recovery file is retained with a recorded SHA-256; rollback was not needed.

The main lesson is that desired state, evaluator state and notification delivery are separate evidence claims. Milestone 030 establishes the first two, while notification delivery and independent monitoring remain deliberately deferred. Next: observe natural behavior rather than manufacturing a failure, then revisit the trial delays before considering delivery.


---

## 2026-09-11 - Milestone 032

### What I worked on

Built and deployed Forge YAML Workbench, a browser-local Kubernetes manifest inspector with multi-document parsing, formatting, human-readable summaries, bounded operational findings, and an expandable object tree.

### What I learned

- A static browser application can provide useful manifest review without Kubernetes credentials, backend storage, or server-side processing.
- Release safety improves when source tests, multi-architecture image builds, immutable digests, server-side dry-run, live diff, and explicit deployment approval remain separate gates.
- A formatter must round-trip multi-document input; preserving a document's existing start marker while also joining documents with `---` can silently create an empty document.
- Browser acceptance catches interaction defects that source-level tests may miss. The failed test directly produced a sixth regression test and corrected patch release.
- Idempotent UI actions may need visible confirmation even when they succeed and produce little visual change.

### What was difficult

The first `0.1.0` deployment was healthy at the container and Kubernetes layers, but clicking Format on the sample exposed an application defect. The YAML library preserved the second document's start marker, while the formatter added another separator. That created an empty Document 2 despite the original sample being valid.

Windows `kubectl diff` also required Git for Windows' bundled `diff.exe` to be added temporarily to `PATH`. Keeping the investigation read-only until each mutation was separately approved preserved a clear operational boundary.

### What I finished

- Added locked Node dependencies, six analyzer tests, CI, audit, and AMD64/ARM64 container validation.
- Published versioned images through a guarded tag workflow without a floating `latest` tag.
- Deployed a restricted, non-root, read-only Workbench with no Kubernetes identity or persisted YAML.
- Published and pinned corrected release `0.1.1` at OCI index digest `sha256:50e3d115641941bc8f7eaa303463c08ccbafe5842cc07304d4b71dbd4aef8669`.
- Verified one Ready replica with zero restarts, matching runtime ImageID, NodePort health, security headers, and browser behavior.
- Confirmed multi-document formatting retains the Deployment and Service, and visibly reformatted flow-style YAML remains valid.

### Next small step

Complete final review and merge of PR #8 with explicit approval. Treat any positive format-status message or broader schema validation as a separate future increment.


---

## 2026-09-12 - Milestone 033 Workbench usability and 0.1.2 rollout

### What I worked on

Improved Forge YAML Workbench interaction clarity and diagnostic precision without changing its browser-local trust boundary. The release adds explicit action feedback, clickable parser locations, filename preservation, keyboard shortcuts, protected clearing, accessible tab state, and DOM interaction tests.

### What I learned

- Small browser acceptance tests expose usability defects that analyzer tests cannot see; the first diagnostic-navigation pass found stale red feedback after the YAML was corrected.
- Idempotent actions still need explicit confirmation. Reporting that YAML is already formatted removes ambiguity without changing the document.
- Release publication, immutable digest pinning, server-side dry-run, live diff review, deployment approval, rollout verification, and browser acceptance are distinct evidence gates.
- A runtime ImageID matching the reviewed OCI index digest proves the cluster is running the approved multi-architecture release rather than merely trusting its tag.

### What I finished

- Expanded automated coverage to 12 analyzer and DOM interaction tests.
- Published `0.1.2` for AMD64 and ARM64 without a floating tag.
- Pinned OCI index digest `sha256:07f34be33c55bca5b7bf5321e5d149e4831ce520c9efbdd98233468a1a50e3c7`.
- Rolled out only the approved Workbench Deployment and verified one Ready replica with zero restarts.
- Verified the ready EndpointSlice, NodePort health, security headers, and all seven live browser smoke checks.

### Next small step

PR #9 merged at `7aadedd`. Begin Milestone 034 as a separate bounded change for deeper deterministic Kubernetes checks with precise YAML paths and suggested corrections.

---

## 2026-09-13 - Milestone 034 deterministic checks and actionable remediation

### What I worked on

Expanded Forge YAML Workbench from parser-focused feedback into a bounded Kubernetes manifest inspection tool. Findings now include clickable YAML paths, plain-language risk explanations, recommended changes, copyable YAML examples, operational cautions, and initial OWASP Kubernetes Top 10:2025 K01 references. Deterministic cross-document checks cover workload selectors, duplicate identities, Service selection, named target ports, host namespaces, container hardening, and seccomp configuration.

### What I learned

- A finding becomes substantially more useful when it identifies the exact field, explains why it matters, and shows a reviewable correction.
- Missing-field diagnostics need to navigate to the nearest existing parent because the desired line does not yet exist.
- Browser-local analysis can provide meaningful operational guidance while maintaining an explicit boundary around Kubernetes schema, admission, and cluster-context claims.
- Publishing, digest pinning, server-side dry-run, diff review, deployment approval, runtime verification, and browser acceptance remain separate evidence gates.

### What I finished

- Expanded automated coverage to 23 analyzer and DOM interaction tests.
- Published `0.2.0` for AMD64 and ARM64 without a floating tag.
- Pinned and verified OCI index digest `sha256:1be3942fc9acf62906b020872d31a61cc6e1dab4e879476b4ba233063fb57720`.
- Rolled out only the approved Workbench Deployment and verified one Ready replica with zero restarts.
- Verified EndpointSlice routing, NodePort health, security headers, clickable paths, expandable fix guidance, clipboard examples, cautions, and OWASP references in the live application.

### Next small step

Complete final review and merge of PR #10. Begin General YAML inspection mode as Milestone 035 in a new chat, leaving Kubernetes schema validation and broader OWASP coverage for Milestones 036 and 037.

---

## 2026-09-13 - Milestone 035 General YAML inspection

### What I worked on

Added an explicit General YAML inspection mode beside the existing Kubernetes mode. Kubernetes remains the startup default, and switching modes preserves the editor contents while reusing the same browser-local parser, formatter, diagnostics, file handling, and document tree.

### What I learned

- Parsing and presentation boundaries can be separated cleanly: both modes share syntax handling, while only Kubernetes mode performs resource interpretation and operational checks.
- General YAML needs to treat mappings, sequences, and scalars as valid document roots instead of assuming every document represents an object.
- Explicit mode labels and report-boundary text prevent a successful General YAML parse from being mistaken for Kubernetes validation.

### What I finished

- Added mapping, sequence, and scalar summaries for General YAML.
- Suppressed Kubernetes-only findings, remediation guidance, and OWASP references outside Kubernetes mode.
- Preserved Kubernetes behavior as the tested default.
- Expanded analyzer and browser interaction coverage from 23 to 30 passing tests.
- Released package metadata as `0.3.0`.
- Passed pull-request CI and the non-publishing AMD64/ARM64 image build.
- Published approved image `wmstipes/signalforge-yaml-workbench:0.3.0` through GitHub Actions.
- Verified the registry's AMD64 and ARM64 manifests and recorded OCI index digest `sha256:3abd4292f6cbd506dbc976924d2b61cf8093a7653e02654efaedc207e3f3086f`.
- Reviewed the server-side dry-run and live Deployment-only diff before applying the approved candidate.
- Deployed matching `0.3.0` version labels and the immutable OCI index digest with one Ready replica, zero restarts, and a matching runtime ImageID.
- Verified ready routing, HTTP 200 health and page responses, both mode markers, and the expected security headers.
- Completed live browser acceptance for both modes, including content-preserving switches, Kubernetes-finding suppression, and mapping, sequence, scalar, and explicit null roots.
- Merged PR #11 at `b45ee0b` after all checks and approval gates passed.

### Next small step

Begin Milestone 036 as a separate bounded increment for browser-local Kubernetes schema validation against one pinned Kubernetes version. Report unsupported resources and unavailable CRD schemas explicitly, preserve General YAML behavior, and keep publication, deployment, and merge as separately approved checkpoints.

---

## 2026-09-13 - Milestone 036 browser-local Kubernetes schema validation

### What I worked on

Added an offline Kubernetes schema layer to Forge YAML Workbench while retaining the browser-only trust boundary. Kubernetes remains the default mode. The Validation report now separates YAML syntax, Kubernetes document shape, deterministic operational review, and schema results. General YAML continues to provide syntax and structure inspection without Kubernetes findings.

### What I learned

- A schema-valid result needs an exact version and support-set label; without both, it can imply broader compatibility than was actually tested.
- Unsupported built-in resources and custom resources with unavailable CRD schemas are knowledge-boundary states, not successes or failures.
- Kubernetes `IntOrString` fields need explicit normalization when consuming the pinned OpenAPI v2 document through a JSON Schema validator.
- Bundling only the transitive definitions for an explicit GVK set keeps the static application bounded while preserving offline operation.

### What I finished

- Pinned the source schema to Kubernetes `v1.36.4` and recorded the upstream SHA-256.
- Added reproducible generation of a 12-GVK, 196-definition browser bundle.
- Added explicit `valid`, `invalid`, `unsupported`, `schema-unavailable`, and `not-evaluated` states.
- Added clickable schema-error paths and clear UI category separation.
- Preserved General YAML behavior and the absence of Kubernetes schema findings in that mode.
- Expanded automated coverage from 30 to 42 passing tests, including compilation of every supported schema.
- Passed the production build, dependency audit, and whitespace validation.
- Published draft PR #13 and passed Workbench CI plus the non-publishing AMD64/ARM64 container build.
- Published the separately approved `0.4.0` OCI index at `sha256:96e3d8e4a1b563d5d719521bbd8f0d5f6f3e3a5fc3a299851d21186a20de3477` and verified active Linux AMD64 and ARM64 manifests.
- Applied the separately reviewed Deployment-only update and verified one Ready Pod with zero restarts, the expected runtime image digest, one ready endpoint, HTTP 200 health and page responses, and the expected CSP and `nosniff` headers.
- Found a blank-page defect during live browser acceptance: AJV's runtime schema compiler uses dynamic code generation, which the production `script-src 'self'` policy correctly blocks.
- Kept the strict CSP unchanged and prepared a local `0.4.1` correction that checks in reproducible standalone validators generated at build time.
- Added a production-bundle guard that fails if `eval` or `new Function` is present; all 42 tests, the production build, validator reproducibility, and the dependency audit pass locally.
- Published the separately approved `0.4.1` correction in run `34780773917`; its active AMD64/ARM64 OCI index is `sha256:96c715c938f1636686190e294829c61f0f7af71117b353bd2df05a9fc67bddf2`.
- Reviewed the server-side dry-run and live diff, then deployed the separately approved immutable `0.4.1` index.
- Verified one Ready Pod with zero restarts, the exact runtime ImageID, one ready EndpointSlice, HTTP 200 health and page responses, and the unchanged CSP and `nosniff` headers.
- Repeated browser acceptance successfully across Kubernetes and General YAML modes, including schema-valid, schema-invalid, unsupported, unavailable-CRD, and YAML-syntax states.
- Marked PR #13 ready only after browser acceptance; it merged at `fc16ad1`.

### Next small step

Begin Milestone 037 as a bounded, pinned OWASP Kubernetes Top 10:2025 review profile. Preserve browser-local processing and label direct, partial, and cluster-context-required coverage explicitly.

---

## 2026-09-13 - Milestone 037 pinned OWASP Kubernetes review profile

### What I worked on

Expanded Forge YAML Workbench from individual K01 references into a ten-category OWASP Kubernetes Top 10:2025 review profile pinned to an exact upstream commit.

### What I learned

- Coverage and outcome are different concepts: a category can have direct or partial manifest visibility without passing a security assessment.
- Effective RBAC, admission, networking, component, authentication, cloud, audit, logging, and monitoring state cannot be inferred safely from a pasted file.
- One manifest condition can inform multiple risks, so the UI needs shared mappings without duplicating the underlying finding.
- Zero matching signals must be labeled explicitly as “not a pass result.”

### What I finished

- Pinned all ten OWASP category links to upstream commit `828cfa2e2d7af63cdf7025c09ca871265d71f59c`.
- Labeled K01 direct; K02-K06, K08, and K09 partial; and K07 plus K10 cluster-context-required.
- Added bounded RBAC, Secret-environment, Namespace policy-label, external-exposure, and literal cloud-credential findings.
- Added shared K01/K09 and K03/K08 mappings.
- Rendered the ten-category profile after the existing syntax, operational, and schema sections.
- Preserved General YAML suppression and the no-backend, no-cluster-access boundary.
- Expanded automated coverage from 42 to 49 passing tests.
- Passed validator reproducibility, the 706.33 kB / 110.42 kB gzip production build, the CSP scan, zero-vulnerability dependency audit, repository manifest validation, and whitespace validation.
- Published draft PR #14 after explicit approval; all 19 remote files matched the verified local contents and all three non-publishing workflows passed.
- Published the separately approved `0.5.0` AMD64/ARM64 image in run `34787257312`.
- Verified OCI index `sha256:11e8fcc4989fe7dcdc1c5312786b80189a98b6a9acb82e979aa8235d756fcb8e`, AMD64 manifest `sha256:2a47101b9f176671e0954ca55e90b7ae4dfe42ba4b7ce5856ccd2f447822032e`, and ARM64 manifest `sha256:f1de89162f2de896d8907e2fcce17d511246881c919fa15e6ee3a1ea3f6077b3`.
- Staged and separately deployed the immutable `0.5.0` candidate.
- Verified the live Pod is Ready with zero restarts, its configured and runtime ImageID match the reviewed OCI index, the EndpointSlice has one ready address, `/healthz` and the page return HTTP 200, and the strict security headers remain present.
- Browser acceptance confirmed the OWASP profile and General YAML isolation, then found that a YAML path or line/column control selected the correct text without scrolling the editor to it.
- Added centered editor scrolling and a long-manifest browser regression test as local patch candidate `0.5.1`; 50 tests, production build, and CSP scan pass.
- Published the separately approved `0.5.1` AMD64/ARM64 patch image in run `34789023192`.
- Verified OCI index `sha256:4011478de37f9316d65985f17d87d3652203e2bcffd75ee29646ddcd52a64ffa`, AMD64 manifest `sha256:ebad025531960fa9d18a67fd153aa4fd2c56556df87574f06db083564981d5d5`, and ARM64 manifest `sha256:bfabd7f46865db81a8d8b57954dc4c0c2ddcb01a7705390b3e633b6acb2e8238`.
- Staged and separately deployed the immutable `0.5.1` patch.
- Verified the corrected Pod is Ready with zero restarts, its configured and runtime ImageID match the reviewed OCI index, health and page requests return HTTP 200, and the strict security headers remain present.
- Repeated live browser acceptance and confirmed finding links now automatically scroll to and select the correct YAML location.
- Marked PR #14 ready only after corrected browser acceptance, then squash-merged it at `dd46a08`.
- Post-merge Workbench CI run `34789967588`, Kubernetes manifest validation run `34789967652`, and Restaurant API Docker build run `34789967657` passed on `main`.

### Next small step

Select the next bounded milestone from the roadmap while preserving the Workbench trust boundary and gated release workflow.

---

## 2026-09-14 - Milestone 038 browser-local formatting preview

### What I worked on

Changed Forge YAML Workbench formatting from immediate editor mutation into an explicit review workflow. Valid formatting changes now produce a line-oriented browser-local preview with before and after line numbers, while Apply, Cancel, and Escape make the mutation boundary visible.

### What I learned

- Formatting and repair are different operations: a deterministic formatter can normalize valid YAML, but malformed YAML must remain unchanged because the intended structure is ambiguous.
- A preview needs to explain newline and line-ending normalization even when the visible YAML lines otherwise match.
- Line-diff alignment needs an explicit work bound so a convenience feature cannot allocate an unbounded matrix.
- Reproducibility checks must compare semantic generated text across platform checkout conventions; CRLF versus LF alone does not make a validator stale.
- Browser acceptance remains valuable even with DOM tests because operator expectations reveal where workflow boundaries need clearer explanation.

### What I finished locally

- Added a line-oriented formatting preview with added, removed, and unchanged states.
- Required explicit Apply before updating the editor and preserved input through Cancel or Escape.
- Added dialog semantics, initial focus, focus containment, and return focus.
- Added normalization metadata and a labeled simplified-alignment fallback.
- Expanded automated coverage to 58 passing tests.
- Passed pull-request CI, validator reproducibility, CSP compatibility, zero-vulnerability audit, repository validation, whitespace validation, and non-publishing AMD64/ARM64 builds.
- Confirmed the generated-validator check and production build on Windows after correcting line-ending portability.
- Completed local browser acceptance for valid formatting changes, Apply, Cancel, and invalid-YAML validation.
- Prepared candidate version `0.6.0`.
- Published the separately approved AMD64/ARM64 image in run `34858580511` and independently verified OCI index `sha256:4166df67190eaaade054be09c91f0ef8a76e832f290f7383fc4e58c7dd7469bc`.
- Verified AMD64 manifest `sha256:f051ce44976c1abdd2076415edc6476ef57cb8c5e2c7cb196cb1391616ab5f0a` and ARM64 manifest `sha256:d5795e44b4553b8bd6b8a96c7ad6e3b574e8b9e7dcdbc80c0ed1f34ef2e01208`.
- Reviewed a successful server-side dry-run and exact Deployment-only live diff before Mike explicitly approved the rollout.
- Deployed immutable `0.6.0` and verified one Ready Pod with zero restarts, a matching configured image and runtime ImageID, and a ready EndpointSlice.
- Verified fresh HTTP 200 responses from `/healthz` and the application page through NodePort `30081`, with the expected CSP and `nosniff` headers.
- Completed live browser acceptance for preview display, unchanged pre-Apply content, Cancel preservation, Apply formatting, invalid-YAML validation behavior, and both inspection modes.
- Merged PR #16 at `4fed28c`; Workbench CI run 107, Kubernetes Manifest Validation run 104, and Restaurant API Docker Build run 53 passed on `main`.

### Next small step

Select the next bounded milestone; Milestone 038 has no remaining release, deployment, acceptance, or merge gates.

## 2026-09-14 — Milestone 039 planning: browser-local Markdown reports

### What changed

- Anchored the milestone to `main` commit `3b562ef0c4be7fc15fd5bd3cbe98e7d5ca73373c` after Milestone 038 closeout.
- Approved a deterministic Markdown report built from the existing browser-local analysis model.
- Defined a review-first workflow with explicit Copy Markdown and Download .md actions.
- Kept full source YAML out of the report and identified clipboard and local download as deliberate trust-boundary crossings.
- Preserved separate gates for implementation, image publication, deployment, live acceptance, and merge.

### Why this matters

The Workbench can become more useful for peer review, change records, and learning evidence without acquiring a backend or cluster credentials. Treating report export as an explicit operator action also makes the boundary visible instead of silently moving manifest-derived information outside browser memory.

### Next small step

Implement the pure report generator and accessible preview workflow on `codex/milestone-039-markdown-report`, then run the complete local validation suite before considering publication.

## 2026-09-14 — Milestone 039 implementation

### What changed

- Added a pure deterministic Markdown generator driven by the existing browser-local analysis result.
- Added a review dialog with explicit Copy Markdown, Download .md, Cancel, and Escape actions.
- Preserved unsaved YAML state and invalidated prepared reports when their YAML, inspection mode, or file context changed.
- Added unit and DOM interaction coverage for the report contract, mode boundaries, export actions, focus behavior, Markdown safety, and filename derivation.
- Advanced the source candidate to `0.7.0` without changing the tracked Deployment or live `0.6.0` runtime.

### What remains gated

The complete local validation suite and browser checks must pass before publication is considered. Image publication, digest pinning, deployment, live acceptance, final documentation, and merge each remain later gates.

## 2026-09-14 — Milestone 039 source acceptance

### Validation result

- All 69 automated tests passed.
- Validator reproducibility, production build, strict-CSP scan, dependency audit, Kubernetes manifest validation, whitespace validation, and clean-worktree checks passed.
- Local browser acceptance passed for Kubernetes and General YAML reports, report review, Copy Markdown, Download .md, Escape cancellation, filename derivation, and unsaved-state preservation.
- Browser review exposed missing visible export confirmation because feedback was rendered behind the modal.
- Added and accepted an in-modal live message plus highlighted **Copied** and **Downloaded** button states.
- Opened draft PR #18; Workbench CI run 108 and the non-publishing AMD64/ARM64 Docker build run 110 passed.

### Gate state

Source acceptance is complete for candidate `0.7.0`. Immutable image publication, digest recording, cluster deployment, live acceptance, and merge remain separately gated.

## 2026-09-14 — Milestone 039 image publication

### What changed

- Received explicit approval to publish Workbench `0.7.0`.
- Workflow run `34886290349` built and pushed the AMD64/ARM64 image from source commit `84123ae842ce85d8e37bd02d8e96f3fb4d9765ae`.
- Recorded immutable OCI index `sha256:f9f5939910382911b23e78609ea5690e617e2a446c3dd707da2c1c6852a8a6d2`.
- Independently confirmed AMD64 manifest `sha256:1bae69ab2d812f6ee2d8209a01afdc31dc98b28d2c5b4e1925edc7847512448e` and ARM64 manifest `sha256:4aa7295d62481d12973cde2d46ba0a258e1858dc5ac192d89a132134178f269d`.
- Kept the running `0.6.0` Deployment unchanged.
- After separate approval, staged matching `0.7.0` labels and the immutable OCI index in the tracked Deployment manifest without applying it to the cluster.

### Next small step

Repository validation and server-side dry-run passed. The live diff contained only the reviewed `0.7.0` labels, immutable image update, and expected generation preview.

## 2026-09-14 — Milestone 039 deployment and live acceptance

### What changed

- Applied only the explicitly approved Workbench Deployment manifest.
- Verified one available Ready Pod on `forge-node-03` with zero restarts and one ready EndpointSlice.
- Confirmed both the configured image and runtime ImageID use the reviewed immutable `0.7.0` OCI index.
- Received fresh HTTP 200 responses from `/healthz` and the application page through NodePort `30081`, with health body `ok`, Content Security Policy, and `X-Content-Type-Options: nosniff`.
- Completed live browser acceptance for Kubernetes and General YAML reports, visible Copy and Download completion states, predictable Markdown download naming, mode isolation, cancellation, and unchanged editor and unsaved state.

### Next small step

PR #18 merged at `1e0c525`. Workbench CI run 136, Kubernetes Manifest Validation run 121, and Restaurant API Docker Build run 55 passed on `main`. Select the next bounded milestone while preserving the browser-local trust boundary and separate release gates.

## 2026-09-14 — Milestone 040 planning: Validation result filters

### What changed

- Anchored the milestone to `main` commit `1a3a4ecf05f9bda5a8c6419267e80d22aa5c76c4` after Milestone 039 cleanup.
- Approved counted All, Errors, Warnings, Notes, and Valid filters for existing Validation entries.
- Kept the tab badge, overall status, OWASP profile, and Markdown report based on the complete analysis.
- Defined ephemeral filter state that persists across edits but resets at mode and input-replacement boundaries.
- Preserved separate gates for implementation, publication, manifest mutation, deployment, live acceptance, PR readiness, and merge.

### Why this matters

The Validation view now combines syntax, document shape, deterministic operations, and schema results. A presentation-only filter makes larger reviews easier without expanding what the Workbench reads, stores, or claims to know.

## 2026-09-14 — Milestone 040 implementation

### What changed

- Added counted Validation controls for All, Errors, Warnings, Notes, and Valid.
- Hid empty filtered sections and added visible-versus-total and filtered-empty explanations.
- Preserved result ordering, finding navigation, fix guidance, OWASP separation, complete status indicators, and complete Markdown reports.
- Preserved the selected filter through YAML edits while resetting it for inspection-mode changes, sample or file loading, and clearing.
- Added keyboard focus, pressed-state, live-feedback, recomputation, reset, empty-result, OWASP, and report-isolation DOM coverage.
- Advanced source metadata to candidate `0.8.0` without changing the tracked Deployment or live immutable `0.7.0` runtime.

### What remains gated

Complete visual browser review and the non-publishing multi-architecture build before considering publication. Branch publication, image publication, manifest mutation, deployment, live browser acceptance, PR readiness, and merge remain separate approval gates.

### Automated validation result

- All 74 tests passed, including filtered finding navigation and Copy YAML behavior.
- Validator reproducibility, production build, strict-CSP scan, zero-vulnerability audit, repository Kubernetes manifest validation, and whitespace validation passed.
- The repository contains no Workbench Deployment diff; accepted immutable `0.7.0` remains the declared and live runtime.
- Docker is unavailable in this workspace, leaving the non-publishing multi-architecture build for the established GitHub pull-request workflow.
- The remote browser could not reach the workspace loopback server, so visual browser acceptance remains a later explicit gate rather than an inferred result.

## 2026-09-15 — Milestone 040 source acceptance

### Validation result

- Draft PR #20 opened from remote source commit `82b291e`.
- Workbench CI run 137 passed all source checks.
- Non-publishing AMD64/ARM64 Docker build run 139 passed without pushing an image.
- A clean Windows dependency installation and all 74 tests passed.
- Operator browser review accepted filter counts, result-level isolation, empty-section behavior, OWASP separation, unchanged complete-analysis indicators, finding navigation, complete report behavior, recomputation during editing, and filter resets.

### Gate state

Source acceptance is complete for candidate `0.8.0`. Image publication, immutable digest recording, tracked-manifest mutation, deployment, live-cluster acceptance, PR readiness, and merge remain separately gated. Accepted immutable `0.7.0` remains live.

## 2026-09-15 — Milestone 040 image publication

### What changed

- Received explicit approval to publish Workbench `0.8.0` from accepted source commit `1d8a487ada5e053ca806e59195f0807d11564351`.
- Created tag `forge-yaml-workbench-v0.8.0` at that exact commit.
- Publication workflow run 141 (`34972448064`) built and pushed the AMD64/ARM64 image successfully.
- Recorded immutable OCI index `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`.
- Independently confirmed AMD64 manifest `sha256:dfbfc92e3d4a074d0a421cc3fdb7937f4288937af291aac71ec9a0dc3786d536` and ARM64 manifest `sha256:2db1d88fe7357452f82256e81a4d56ef52d3ddc72bffe0f31524adab524ce615`.
- Left the tracked Deployment and live immutable `0.7.0` runtime unchanged.

### Next small step

Prepare and review the exact Deployment-only `0.8.0` label and immutable-image diff. Mutating the tracked manifest requires a separate approval before any cluster deployment is considered.

## 2026-09-15 — Milestone 040 deployment and live acceptance

### What changed

- After separate approval, staged the two `0.8.0` version labels and immutable OCI index in the Workbench Deployment and matching repository validator expectation.
- Repository validation, server-side dry-run, and the exact live diff passed before deployment approval.
- Applied only the approved Workbench Deployment and completed the rolling update successfully.
- Verified one Ready Pod on `forge-node-03` with zero restarts and a runtime ImageID matching OCI index `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`.
- Confirmed the EndpointSlice settled to the new Pod only and fresh `/healthz` and application requests through NodePort `30081` returned HTTP 200.
- Confirmed the deployed Content Security Policy and `X-Content-Type-Options: nosniff` header.
- Completed all nine live browser checks for filter counts, level isolation, empty-section behavior, complete-analysis indicators and reports, edit-time recomputation, reset boundaries, navigation, scrolling, guidance, and Copy YAML.

### Trust boundary

The release remains stateless and browser-local. No backend YAML processing, persistence, telemetry, Kubernetes API access, RBAC, ServiceAccount token, cluster credential, or automatic remediation was added.

### Next small step

Perform the final PR-readiness review. PR readiness and merge remain separate approval gates.

## 2026-09-15 — Milestone 040 merge closeout

### What changed

- Confirmed Workbench CI run 141, Kubernetes Manifest Validation run 123, and non-publishing AMD64/ARM64 Docker Build run 144 passed on the final pull-request head.
- After separate approval, marked PR #20 ready for review with only merge remaining gated.
- PR #20 merged into `main` at `6fa5092210633abde28335b76dcad1e085578789`.
- Confirmed post-merge Workbench CI run 142, Kubernetes Manifest Validation run 124, and Restaurant API Docker Build run 57 passed on `main`.
- Marked Milestone 040 complete with immutable Workbench `0.8.0` published, deployed, runtime-verified, and live browser-accepted.

### Next small step

Merge this documentation-only closeout, remove the merged Milestone 040 branches, and select the next bounded increment from the deferred Workbench capabilities.

## 2026-09-15 — Milestone 041 planning and implementation: browser-local YAML tree search

### What changed

- Verified clean `main` at `e1f48d94a3c88e3a459dedc5af3d9d6537940381` and confirmed both merged Milestone 040 remote branches were removed before implementation.
- Approved a bounded Tree-tab search for keys, scalar values, and canonical YAML paths using case-insensitive literal matching.
- Added deterministic document/depth-first indexing, one-node match counts, Previous and Next wrapping, automatic ancestor expansion, match and active-match presentation, and active-result scrolling.
- Added Enter, Shift+Enter, Escape, and Tree-tab Ctrl+F or Cmd+F behavior while preserving native disclosure controls and search-control focus.
- Preserved query recomputation across edits, temporary invalid YAML, formatting, and tab changes; reset it for mode changes, sample/file loading, and confirmed clearing.
- Added helper and Happy DOM coverage for path construction, values and types, literal matching, ordering, navigation, expansion, highlighting, announcements, focus, parser recovery, formatting, and reset boundaries.
- Advanced source metadata to candidate `0.9.0` without changing the tracked Deployment or live immutable `0.8.0` runtime.

### Trust boundary

Tree search consumes only the already parsed in-memory document values. It adds no replacement, regex, Validation-result search, persistence, backend, network access, Kubernetes API access, credentials, remediation, deployment control, or cluster mutation.

### Current validation result

- All 83 automated tests pass.
- Validator reproducibility, production build, strict-CSP scan, zero-vulnerability audit, repository Kubernetes validation, 23 supporting Python tests, and whitespace validation pass.
- The tracked Workbench Deployment and validator expectation remain unchanged at immutable `0.8.0`.
- This workspace has no Docker client; the non-publishing multi-architecture build remains for the established GitHub workflow after publication approval.
- The cloud browser cannot reach the workspace loopback server, so Windows and operator browser review remain explicit source-acceptance checks.

### What remains gated

Source publication, image publication, manifest mutation, deployment, live browser acceptance, PR readiness, merge, and cleanup remain separate approval gates.

## 2026-09-15 — Milestone 041 source acceptance

### Validation result

- Published the accepted source tree through the connected GitHub integration because the workspace HTTPS remote had no Git credentials.
- Verified all 14 uploaded blob SHAs and the assembled tree SHA against local commit `0fae4a6`; connector-authored commit `20800196d202f6a6b58c37dc73bb49ffe529a2d6` has the identical tree and approved `main` parent.
- Opened draft PR #22 against `main`.
- Workbench CI run 143 passed all source checks.
- Non-publishing AMD64/ARM64 Docker build run 145 passed without pushing an image.
- Windows validation passed from a clean lockfile installation with all 83 tests, validator reproducibility, production build, CSP scan, and zero-vulnerability audit green.
- Operator browser review accepted literal key, value, and path matching; counts; navigation; expansion; highlighting; keyboard and accessibility behavior; edits and invalid-YAML recovery; formatting and report isolation; input-replacement resets; cancelled-clear preservation; and default-expansion restoration.

### Gate state

Source acceptance is complete for candidate `0.9.0`. Image publication, immutable digest recording, tracked-manifest mutation, deployment, live-cluster acceptance, PR readiness, merge, and cleanup remain separately gated. Accepted immutable `0.8.0` remains live.

## 2026-09-15 — Milestone 041 image publication

### What changed

- Received explicit approval to publish Workbench `0.9.0` from accepted source commit `b2a946f9e39ab3f7e1a6bc35ad8bd62297902ca9`.
- Created and pushed tag `forge-yaml-workbench-v0.9.0` at that exact commit.
- Publication workflow run 147 (`35003003075`) built and pushed the AMD64/ARM64 image successfully.
- Recorded immutable OCI index `sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581`.
- Independently confirmed AMD64 manifest `sha256:4cd48baf0f913b944efa4206302d828107674f7ea7e20543972479d09866dc86` and ARM64 manifest `sha256:e26f85a206a2b564928e285f34253b72b5c8890f99d2eb0af702bfcfdecc9d7b`.
- Left the tracked Deployment and live immutable `0.8.0` runtime unchanged.

### Next small step

Prepare and review the exact Deployment-only `0.9.0` label and immutable-image diff. Mutating the tracked manifest requires separate approval before cluster deployment is considered.

## 2026-09-15 — Milestone 041 deployment and live acceptance

### What changed

- After separate approval, changed only the Workbench Deployment version labels and immutable image reference to `wmstipes/signalforge-yaml-workbench:0.9.0@sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581` and updated the repository validator expectation.
- Repository validation passed, and the server dry-run completed. The non-fatal Server-Side Apply ownership warning reflected the existing client-side-managed last-applied annotation; the actual rollout retained client-side `kubectl apply`.
- The reviewed live diff contained only generation 12 to 13, two version-label changes, and the immutable image change.
- Deployment generation 13 completed with one available and Ready Pod on `forge-node-03`, zero restarts, and an exact configured/runtime OCI index match.
- EndpointSlice `forge-yaml-workbench-bjzkq` reported ready endpoint `10.244.54.202:8080`. Private-lab NodePort `30081` returned HTTP 200 for `/healthz` and `/`, including the expected CSP, `nosniff`, frame, and referrer headers.
- Operator live browser acceptance passed literal key, scalar-value, and canonical-path search; one-node counts; Previous/Next wrapping; ancestor expansion; match and active-match highlighting; keyboard, focus, and live-status behavior; edit and invalid-YAML recovery; formatting and report isolation; reset boundaries; cancelled-clear preservation; and default-expansion restoration.

### Trust boundary

The deployed search remains entirely browser-local and ephemeral. No YAML content is sent to a backend, and no telemetry, persistence, Kubernetes API access, RBAC, ServiceAccount token, credential, deployment control, automatic remediation, or cluster mutation capability was added to the application.

### Next small step

Review draft PR #22 for readiness. Marking it ready, merging it, and post-merge cleanup remain separate approval gates.

## 2026-09-15 — Milestone 041 PR readiness and folded closeout

### Result

- Received separate approval for PR readiness and for folding substantive closeout documentation into PR #22.
- Recorded the accepted immutable release, Deployment-only mutation, runtime evidence, HTTP and security-header checks, complete live browser workflow, trust boundary, and remaining repository procedure in the milestone record, roadmap, project status, and learning journal.
- Confirmed the post-acceptance documentation commit passed Workbench CI run 147, Kubernetes Manifest Validation run 126, and non-publishing AMD64/ARM64 Docker Build run 150.
- Kept merge as a separate approval gate. GitHub will retain the authoritative merge disposition, so no follow-up documentation PR is required.

### Remaining procedure

After separately approved merge, synchronize `main` and remove the local and remote Milestone 041 feature branch. That cleanup changes no project content.

## 2026-09-15 — Milestone 041 merge and cleanup

### Result

- PR #22 merged into `main` at `0f3d44e2abff204f0019ea6d97bb2ab4b1ffe198` after separate approval.
- The local and remote `codex/milestone-041-tree-search` branches were removed.
- Milestone 041 is complete; immutable Workbench `0.9.0` remains deployed and accepted.

## 2026-09-15 — Milestone 042 planning and local implementation: safe browser-local YAML file drop

### What changed

- Approved a bounded editor drop target for exactly one local `.yaml` or `.yml` file, with case-insensitive extension matching.
- Added persistent visible instructions and a drop-ready overlay using text and a dashed boundary rather than color alone.
- Added file-only drag detection, page-navigation prevention for misplaced drops, and deterministic cleanup for leave, drop, Escape, drag end, and window blur.
- Routed accepted files through the existing input-replacement boundary and preserved the basename for later YAML and Markdown downloads.
- Added one shared unsaved-change confirmation for dropped files, Open file, and Load sample.
- Preserved all state after cancellation, rejection, or read failure; successful replacement preserves the mode and tab, resets Validation filtering and Tree search, invalidates prepared reports, and routes invalid YAML to existing parser diagnostics.
- Advanced source metadata to candidate `0.10.0` without changing the tracked Deployment or live immutable `0.9.0` runtime.
- Reconciled Milestone 041 merge and cleanup status and corrected the Kubernetes README's stale `0.8.0` image details.

### Trust boundary

The browser exposes only the chosen file basename and contents. The Workbench does not receive a filesystem path and adds no upload, network request, backend, telemetry, cookie, browser storage, Kubernetes API access, RBAC, credential, deployment control, or cluster mutation.

### Current validation result

- All 92 automated tests pass, including nine focused file-drop and state-boundary interactions.
- Validator reproducibility, production build, strict-CSP scan, complete zero-vulnerability dependency audit, repository Kubernetes validation, 38 supporting Python tests, and whitespace validation pass.
- The established production bundle-size advisory remains non-blocking.
- This workspace has no Docker client; clean Windows validation, operator browser review, and the non-publishing AMD64/ARM64 build remain release-evidence items.
- The tracked Workbench Deployment and live cluster remain unchanged at immutable `0.9.0`.

### What remains gated

Remote source publication, image publication, manifest mutation, deployment, live browser acceptance, PR readiness, merge, and cleanup remain separate approval gates.

## 2026-09-15 — Milestone 042 source acceptance

### Validation result

- Published `codex/milestone-042-safe-yaml-drop` after explicit approval and opened draft PR #23 against unchanged `main` baseline `0f3d44e2abff204f0019ea6d97bb2ab4b1ffe198`.
- Verified connector-authored commit `ba97289c391cab7e7a33f13efc2ca39103065214` has tree `0c72ff7b8678914338c34e566b2acf02c8592b37`, exactly matching the accepted local source tree.
- Workbench CI run 151 and Kubernetes Manifest Validation run 130 passed.
- Non-publishing AMD64/ARM64 Docker Build run 153 passed; release preparation, Docker Hub login, and publishing were skipped.
- Clean Windows validation passed all 92 tests, validator reproducibility, production build, strict-CSP validation, and the complete zero-vulnerability dependency audit.
- Operator browser review passed visible target instructions and presentation, successful loading and focus, dirty-source cancellation and confirmation, unsupported and multiple-file rejection, misplaced-drop navigation prevention, Open file and keyboard behavior, invalid-YAML routing, and shared replacement safeguards.

### Gate state

Source acceptance is complete for candidate `0.10.0`. Release tag and image publication, manifest mutation, deployment, live-cluster acceptance, PR readiness, merge, and cleanup remain separately gated. Accepted immutable `0.9.0` remains tracked and live.

## 2026-09-15 — Milestone 042 release publication and manifest candidate

### Release evidence

- Received explicit approval to publish Workbench `0.10.0` from accepted source commit `ba97289c391cab7e7a33f13efc2ca39103065214`.
- Created and pushed annotated tag `forge-yaml-workbench-v0.10.0` at that exact commit.
- Docker Build run 154 completed successfully through the tagged publication path.
- Published `wmstipes/signalforge-yaml-workbench:0.10.0` as immutable OCI index `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`.
- Verified active AMD64 manifest `sha256:c8223d013931e0c02a582f372b826cb827eed1d6f2ba887eac7661387ef03fa2` and ARM64 manifest `sha256:a297014f6df7579c25bcaaa6bbea12bb39e398a36828d647228e5859e7b77869`.

### Manifest boundary

- After separate approval, changed only the tracked Workbench Deployment version labels and immutable image reference to `0.10.0` and updated the repository validator expectation.
- Post-mutation verification passed all 92 Workbench tests, validator reproducibility, production build, strict-CSP scan, zero-vulnerability audit, repository manifest validation, all 51 supporting Python tests, and whitespace validation.
- The live cluster remains on accepted immutable `0.9.0`; no server-side dry-run, cluster diff, apply, rollout, or live acceptance action occurred in this gate.
- Publishing the manifest follow-up, reviewing deployment evidence, applying it, and accepting the live application remain separately gated.

## 2026-09-15 — Milestone 042 deployment and live acceptance

### Deployment evidence

- Repository validation and server-side dry-run passed before deployment.
- The reviewed live diff contained only generation 13 to 14, the Deployment and Pod-template version labels changing from `0.9.0` to `0.10.0`, and the image changing to immutable OCI index `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`.
- After separate approval, applied only `k8s/forge-yaml-workbench/forge-yaml-workbench-deployment.yaml`.
- Deployment generation 14 completed with one available and Ready Pod `forge-yaml-workbench-68856b4c5d-jvtgx` on `forge-node-03`, zero restarts, and an exact configured/runtime digest match.
- EndpointSlice `forge-yaml-workbench-bjzkq` exposed one ready endpoint at `10.244.54.203:8080`.
- NodePort `30081` returned HTTP 200 for `/healthz` and `/` with the expected CSP, `nosniff`, frame-denial, and referrer-policy headers.

### Live browser acceptance

- The deployed page identified release `0.10.0` and exposed visible, accessible file-drop instructions and presentation.
- Successful drops loaded YAML, announced the basename, and focused the editor.
- Dirty-source cancellation preserved YAML, mode, tab, and search state; confirmed replacement preserved mode and tab while resetting Tree search.
- Unsupported and multiple-file drops were rejected without replacement, and misplaced drops did not navigate the browser.
- Invalid YAML entered the established Validation path; Ctrl+O and Load sample retained the shared unsaved-change safeguard; downloads preserved the opened basename.

### Gate state

Immutable Workbench `0.10.0` is published, deployed, runtime-verified, and live browser-accepted. PR #23 remains draft; PR readiness, merge, and cleanup remain separately gated.

## 2026-09-15 — Milestone 042 merge

### Result

- Marked PR #23 ready only after the accepted release, Deployment-only rollout, runtime evidence, live browser acceptance, closeout documentation, and all final workflows were complete.
- Reconciled the PR description with the published OCI digest, generation-14 runtime, browser acceptance, trust boundary, and remaining procedural gates.
- PR #23 merged into `main` at `020d5e796d586b12b9e5e2819cb898d0c51dcaf9` after separate approval.
- Milestone 042 is complete; only integration of this post-merge status record and separately approved branch cleanup remain.

## 2026-09-15 — Milestone 043 planning and local implementation

### Result

- Audited the README, roadmap, architecture, project status, all milestone records, both runbooks, current workflows, and GitHub's documented Wiki behavior before selecting the increment.
- Kept the repository authoritative and bounded the Wiki to a repository-owned Home and custom sidebar that route distinct readers to current repository documents.
- Added a standard-library validator and seven focused tests for file scope, heading structure, descriptive same-repository links, local target existence, the authority notice, volatile-content rejection, exact Wiki-copy comparison, and the intended Restaurant image-workflow event matrix.
- Corrected the Restaurant API Docker workflow candidate so documentation-only `main` pushes do not publish an image while application-source pushes, version tags, and manual dispatch remain enabled.
- Reconciled the stale project-status next step and documented the authority, maintenance, accessibility, validation, and approval boundaries.
- Local implementation is complete. No branch publication, draft PR, Wiki mutation, PR readiness transition, merge, or cleanup has been authorized.

## 2026-09-15 — Milestone 043 publication, acceptance, merge, and cleanup

### Result

- Published the reviewed Home and sidebar as exact copies at Wiki commit `0a945b4cac2ba1c781a55f9aa1a8c389426892e3`.
- Browser acceptance passed visible rendering, all destinations, keyboard navigation, readability at 200-percent zoom, and collaborator-only editing.
- PR #25 merged at `c42614db59f8b42a3d5e90d0a9e4272f47ed8080`; the documentation-only merge did not trigger the Restaurant API image workflow.
- PR #26 merged the closeout evidence at `90c4b369516881943ed3c00d1070f7c70b5fc7ae`.
- After separate approval, all `codex/milestone-*` branches were removed locally and remotely. The older `feature/foundry-check-cli` and `feature/project-status` remote branches remain intentionally preserved.

### Lesson

A reader-facing documentation layer can improve navigation without becoming a second source of truth when its content is deliberately stable, repository-owned, validated, and published through an exact-copy contract.

## 2026-09-16 — Milestone 044 planning and local implementation: ForgeOps read-only health snapshot design

### Result

- Reconciled the roadmap's first ForgeOps outcome with the actual operator tools, application state, workflows, and runbooks.
- Confirmed that `forge.ps1 status` is unstructured and shares a dispatcher with mutating commands, while `forge.ps1 smoke` creates and deletes a temporary Pod.
- Selected a separate future local collector instead of extending that mixed read/write command boundary.
- Defined explicit kubeconfig and context targeting, fixed SignalForge resource identities, stable ordering, `PASS`/`WARN`/`FAIL`/`UNKNOWN` semantics, exit codes, timeouts, redaction, and fail-closed incomplete-collection behavior.
- Limited the first contract to the four expected nodes; five named Deployments and their Pods; allowlisted EndpointSlices; Metrics APIService availability; and explicitly configured Restaurant API and Workbench GET endpoints.
- Excluded logs, Events, Secrets, ConfigMaps, broad discovery, temporary Pods, port-forwarding, arbitrary API paths, AI reasoning, remediation, and all mutation.
- Defined offline fixture tests and a deny-by-default command-runner test before any future implementation can receive read-only live acceptance.
- Reconciled Milestone 043 publication, merge, closeout, and cleanup status across current documentation.

### Current validation boundary

- Milestone 044 changes documentation only.
- No collector code, workflow, package version, image, Kubernetes manifest, runbook command, Wiki source, live Wiki, or cluster resource changes.
- Branch publication and draft PR creation completed after separate approval at commit `c0cbfab`; the published and reviewed local trees matched exactly at `f542f306`.
- Separately approved live feasibility used only the fixed read-command allowlist and five explicit HTTP GETs. It did not create a Pod, read logs, inspect Secrets or ConfigMaps, start a port-forward, publish a report, or mutate a resource.

### Live feasibility result

- The exact `kubernetes-admin@kubernetes` context resolved from one explicit operator-configured kubeconfig.
- All four expected nodes were Ready with one `Ready` condition each.
- Restaurant API, Prometheus, Grafana, Forge YAML Workbench, and Metrics Server met their expected desired, updated, ready, and available replica counts.
- Seven selected Pods were Running and Ready with zero restarts; the three Restaurant API replicas reported one consistent runtime image digest.
- Restaurant API exposed three ready endpoints; Prometheus, Grafana, and Workbench exposed one each; no selected endpoint was not-ready or unknown.
- `v1beta1.metrics.k8s.io` had one available condition with status `True`.
- Restaurant API `/version`, `/health`, `/ready`, and `/status` plus Workbench `/healthz` returned HTTP 200 and their expected bounded fields or body without redirects.
- The combined result corresponds to exit code `0`: required evidence was complete and every evaluated expectation passed.

### Lesson

The first manual preflight correctly stopped before collection when an assumed default Windows kubeconfig path did not exist. Because commands pasted individually continue after each terminating error, later empty displays were cascade artifacts rather than health evidence. Resolving the already configured `KUBECONFIG` entry, requiring an exact context match, and running the acceptance commands as one atomic block produced the valid result. The future collector must preserve that fail-closed behavior without depending on a platform-specific default path.

### Next small step

Proceed through separately gated PR readiness and merge, then record the final merge evidence before cleanup.

## 2026-09-16 — Milestone 044 merge and closeout

### Result

- Marked PR #27 ready only after offline validation, exact local/remote tree comparison, and separately approved read-only live feasibility passed.
- PR #27 merged into `main` at `c467468f8afa349af92f6af1601283449248c8a4` on 2026-09-16 at 10:57:27 EDT.
- Confirmed the merge contains branch head `f42bc7520c3bce572a651415306776841e6dd6a6` and that both resolve to tree `4a445e26526c207e1e766b1d42c5adf23b647bfc`.
- The operator confirmed all Actions displayed by GitHub were green. The connected GitHub API exposed no workflow-run or commit-status records for the head or merge commit, so no run identifiers or unsupported status claims are recorded.
- Milestone 044 is complete as a design milestone. It introduced no collector code, package, image, workflow, manifest, deployment, Wiki change, or cluster mutation.

### Lesson

Evidence sources can disagree in visibility without disagreeing on outcome. The operator-visible GitHub checks were green, while the connected API returned no associated run or status records. Recording both observations preserves provenance instead of manufacturing missing identifiers.

### Next small step

Milestone 044 closeout merged through PR #28 at `aa178b0a4f63a4680d9f47063aec817807b9771e`, and both milestone branches were removed locally and remotely. Proceed with the separately approved Milestone 045 implementation of the accepted collector contract.

## 2026-09-16 — Milestone 045 local implementation: deterministic read-only snapshot

### Result

- Implemented a separate `forgeops snapshot` Python command while preserving the earlier `foundry-check` utility.
- Encoded the four Nodes, five Deployments and Pod selectors, four Services, Metrics APIService, and five optional HTTP paths as fixed constants rather than user-selectable resources.
- Added a deny-by-default kubectl runner that uses argument arrays with `shell=False`, explicit kubeconfig and context arguments, ten-second calls, and two-MiB output limits.
- Added a no-redirect HTTP runner for explicit operator URLs with five-second calls, 64-KiB bodies, and credential-bearing URL rejection.
- Reduced Kubernetes and HTTP responses to accepted fields before deterministic evaluation or rendering.
- Implemented stable `PASS`, `WARN`, `FAIL`, and `UNKNOWN` checks with exit codes `0`, `1`, and fail-closed `2`.
- Added equivalent terminal and Markdown renderers that state their scope and redaction boundary without claiming continuous monitoring or complete cluster health.
- Added synthetic healthy and failure fixtures, focused offline tests, and a dedicated CI workflow with no cluster credentials or live access.
- Added the ForgeOps operator runbook and reconciled Milestone 044 closeout and cleanup status.

### Validation boundary

- Local implementation runs entirely from synthetic fixtures; no kubectl command, HTTP endpoint, cluster resource, Wiki, registry, image, or deployment was contacted or changed.
- Package metadata advances locally from `0.1.0` to `0.2.0` to expose the second command; no distribution is published.
- Publication, read-only live acceptance, PR readiness, merge, closeout, and cleanup remain separate gates.

### Lesson

The safest place to constrain an operational collector is before subprocess execution: typed operations and fixed target mappings make unsupported commands unrepresentable, while selected-field normalization keeps complete API objects out of later evaluation and reports.

### Next small step

Review the complete local diff and offline validation evidence. Publish the branch and open a draft PR only after separate approval.
