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

### Next small step

Prepare the digest-pinned manifest and read-only deployment review. Applying the Deployment still requires explicit approval.
