# Project Status

**Last updated:** 2026-09-22

**Current phase:** ForgeOps v1.0.0 supported baseline

## Summary

The active Foundry workstream is SignalForge, a four-node Raspberry Pi Kubernetes lab. The cluster runs the versioned SignalForge Restaurant API, lightweight Prometheus, Kubernetes Metrics Server, Grafana, and the browser-local Forge YAML Workbench.

The project has moved from basic workload deployment into repeatable engineering operations: automated tests, GitHub Actions, ARM64 image publishing, version-controlled Kubernetes manifests, validation, helper commands, application metrics, and current node and Pod resource visibility. Milestones 044-050 established bounded snapshot collection, deterministic evidence, validation, comparison, and a synthetic scenario corpus. Milestone 051 established explicit ForgeOps execution identity and supported local execution modes. Milestone 052 added exact-byte evidence integrity records without claiming authenticity or chain of custody. Milestone 053 added bounded offline scenario replay. Milestones 054-056 established strict runbook knowledge, deterministic grounded mapping, and the bounded incident-reasoning design. Milestones 057-060 implemented strict mapping validation, deterministic structured briefing, exact replay, and a fixed operator text view. Milestone 061 adversarially evaluated those boundaries and deferred model and retrieval integration. Milestone 062 passed its synthetic and live read-only incident-copilot demonstration without expanding that authority or identifying a concrete unmet operator question. Milestone 063 defined the bounded release contract, Milestone 064 proved the exact candidate, and Milestone 065 published and independently accepted ForgeOps v1.0.0.

The [testing and validation guide](testing-and-validation.md) defines current
suite counts, collection scope, commands, offline and live boundaries, and the
maintenance rule for future test changes. Historical milestone counts remain
historical evidence rather than being rewritten when the suite grows.

## Current ForgeOps Console state

- Planning work package: [C5 reviewed evidence boundary](milestones/forgeops-console-c5-evidence-boundary-planning.md);
  planning requested, implementation approval pending. ForgeFire is captured
  as a separate future proposal; no fault injection is authorized.
- Accepted work package: C4 bounded Pod diagnostics
- Status: accepted through PR #103 at `7910f0a`; published CI passed and the
  separately authorized bounded live walkthrough passed on 2026-09-21
- Intended form: local browser application served by a loopback-only Go core
- Configuration: one explicit kubeconfig path and one operator-selected context;
  no ambient or in-cluster credential fallback
- Current authority: fixed typed list/read projections for Namespace, Node,
  Deployment, ReplicaSet, Pod, Service, and EndpointSlice
- C3 live evidence: separately authorized, operator-run SignalForge walkthrough
  passed on 2026-09-21 against laptop source `82741388`; all six resource views,
  owner/selector relationships, and scope reset/reselection were observed.
  This does not establish concurrent cancellation, every error/security path,
  or application network reachability; see the [C3 milestone](milestones/forgeops-console-c3-read-only-resource-browser.md#live-read-only-walkthrough--2026-09-21)
- Plugin boundary: inert example, resource-browser, and diagnostics compiled first-party
  plugins constrained by a strict, versioned, deny-by-default capability broker
- ForgeOps boundary: v1.0.0 remains unchanged and independently usable;
  Console activity is not ForgeOps evidence
- Runtime impact: local Windows build and loopback Console performed approved
  live Kubernetes reads; no package/image publication, deployment, application
  endpoint check, or cluster mutation was part of this walkthrough
- Open usability follow-up: C3-UX-01, clarify the Node `Scheduling` label;
  implementation is deferred and tracked in the C3 milestone
- C4 authority: selected-Pod bounded log/Event snapshots and offline
  PowerShell/POSIX command previews through `forge.diagnostics`; no commands
  are executed
- C4 live evidence: operator-tested Windows build at `7910f0a`; one current
  container log snapshot displayed with a safety-limit warning; Pod Events
  returned no matches; both previews and clear/scope-reset checks passed.
  The operator confirmed the Console stopped. No raw logs or screenshots are
  committed; this does not prove every error path or in-flight cancellation.
- C4 validation and gate disposition: see the
  [C4 milestone](milestones/forgeops-console-c4-pod-diagnostics.md); no release,
  image, deployment, persistent state, or ForgeOps evidence integration added
- Direction: the separately gated C1-C7 sequence is documented in
  `docs/roadmaps/forgeops-console-roadmap.md`

## Current application

- Application: SignalForge Restaurant API
- Namespace: `forge-restaurant`
- Deployment: `restaurant-api`
- Replicas: 3
- Release: `0.7.0`
- Image: `wmstipes/signalforge-restaurant-api:0.7.0`
- External lab access: NodePort `30080`
- Metrics endpoint: `/metrics`

## Current Forge YAML Workbench state

- Application: Forge YAML Workbench
- Namespace: `forge-tools`
- Deployment: `forge-yaml-workbench`
- Replicas: 1 available and Ready
- Release: accepted `0.10.0` deployed
- Image: `wmstipes/signalforge-yaml-workbench:0.10.0@sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`
- Runtime ImageID: verified against the pinned OCI index digest
- External lab access: NodePort `30081`
- Data path: browser-local parsing and analysis; no server-side YAML persistence
- Modes: Kubernetes inspection by default and explicit General YAML inspection for mapping, sequence, and scalar roots
- Kubernetes identity: no mounted ServiceAccount token and no RBAC access
- Security: restricted namespace, non-root execution, RuntimeDefault seccomp, read-only root filesystem, and all capabilities dropped
- Acceptance: immutable `0.10.0` is deployed; generation 14, configured and runtime digests, one Ready Pod on `forge-node-03` with zero restarts, one ready EndpointSlice endpoint, NodePort health and page responses, security headers, and the complete live file-drop workflow passed
- Validation filters: counted All, Errors, Warnings, Notes, and Valid views preserve the complete analysis for the tab badge, overall status, OWASP coverage, and Markdown reports
- Tree search: Milestone 041 provides literal key, scalar-value, and canonical-path matching with deterministic counted navigation, automatic ancestor expansion, highlighting, accessible keyboard behavior, and explicit state boundaries
- File drop: Milestone 042 provides visible one-file YAML drag-and-drop, shared unsaved-change protection, explicit state preservation and reset boundaries, keyboard-equivalent opening, and browser-navigation prevention

## Current documentation front-door state

- Milestone: 043, complete and cleaned up
- Purpose: curated navigation for recruiters, technical reviewers, operators, and learners
- Authority: repository documentation remains authoritative
- Repository source: `docs/wiki/Home.md` and `docs/wiki/_Sidebar.md`
- Validation: offline structure, link-target, stable-content, workflow-trigger, exact-copy, and browser checks passed
- Live Wiki: published and accepted at `0a945b4cac2ba1c781a55f9aa1a8c389426892e3`
- Repository merge: PR #25 merged at `c42614db59f8b42a3d5e90d0a9e4272f47ed8080`; closeout PR #26 merged at `90c4b369516881943ed3c00d1070f7c70b5fc7ae`
- Restaurant API image workflow: documentation-only `main` pushes now skip publication, while Restaurant API source changes, version tags, and manual dispatch remain enabled
- Cleanup: all `codex/milestone-*` branches were removed locally and remotely; the intentionally preserved older remote branches are unchanged

## Current ForgeOps state

- Milestone: 044, design complete and merged through PR #27 at `c467468`
- Goal: define a separate local, read-only SignalForge health snapshot before implementation
- Target evidence: expected nodes, five named Deployments and their Pods, allowlisted EndpointSlices, Metrics APIService availability, and explicitly configured application endpoints
- Output contract: one normalized `forgeops.snapshot/v1alpha1` model with equivalent terminal, Markdown, and locally implemented JSON views
- Safety boundary: explicit kubeconfig and context, closed read-command allowlist, bounded output, redaction, no broad discovery, no sensitive objects, and no mutation
- Failure boundary: incomplete required evidence remains `UNKNOWN` and returns an incomplete-collection exit code rather than implying health
- Publication: branch `codex/milestone-044-forgeops-snapshot-design` contained design commit `c0cbfab` and live-evidence reconciliation commit `f42bc75`; the published and locally reviewed head trees matched exactly at `4a445e26`
- Live feasibility: exact context validation passed; four expected nodes were Ready; all five Deployments met desired, updated, ready, and available replica counts; seven selected Pods were Running and Ready with zero restarts; all expected EndpointSlice endpoints were ready; Metrics APIService was available; and all five bounded HTTP checks passed
- Runtime impact: read-only Kubernetes and HTTP feasibility queries only; there is no collector implementation, image, manifest, deployment, rollout, restart, Wiki mutation, or cluster mutation in this milestone
- Merge: PR #27 was marked ready after separate approval and merged into `main` at `c467468f8afa349af92f6af1601283449248c8a4` on 2026-09-16; the merge tree exactly matched the reviewed branch tree
- Checks: the operator confirmed all Actions shown in GitHub were green; the connected GitHub API exposed no workflow-run or commit-status records for either the head or merge commit
- Closeout and cleanup: closeout PR #28 merged at `aa178b0`; both Milestone 044 branches were removed locally and remotely
- Milestone 045: deterministic `forgeops snapshot` implementation complete and merged through PR #29 at `3e9851d`
- Implementation: fixed SignalForge constants, deny-by-default kubectl and HTTP runners, selected-field normalization, deterministic evaluation, and terminal, Markdown, or JSON rendering
- Test boundary: synthetic fixtures only; no test invokes kubectl or contacts a network
- Local package metadata: Milestone 045 introduced `0.2.0`; Milestone 046 advanced it to `0.3.0` for the JSON output contract while preserving `foundry-check`
- Publication: PR #29 branch head `377b843`; reviewed branch and merge trees matched exactly at `c879d164e726a20c418e48eb931731102e61d51e`
- CI: ForgeOps CI runs `35128781478` and `35129577800` passed before merge; post-merge push run `35129953752` passed on `main`
- Live acceptance: exact published commit and tree verified; 33 checks passed with no warnings, failures, or unknowns and exit code `0`
- Runtime impact: approved read-only Kubernetes and five explicit HTTP requests only; no image, manifest, deployment, package registry, Wiki, or cluster mutation
- Merge: PR #29 was marked ready after separate approval and merged into `main` at `3e9851da0351e1e01f90c5e38b534e5bbade929d` on 2026-09-16; branch head `377b8439ded59b5f6c48b2bf6b848a991ba2f079` is an ancestor of the merge commit
- Closeout and cleanup: closeout PR #30 merged at `f714d25`; all Milestone 045 branches were removed locally and remotely
- Milestone 046: deterministic JSON evidence contract complete and merged through PR #31 at `4715628`
- JSON boundary: evaluated checks only, fixed key and check order, explicit summary and limitations, no raw response serialization, and no collection-authority change
- Local validation: 33 offline ForgeOps tests pass, including the fixed golden JSON contract, mixed-status precedence, renderer parity, offline CLI rendering, CLI selection, and redaction
- Publication: draft PR #31 opened from published commit `2f49025`; published tree `0f4ac04483b36615a5848cd940b8457203d40c5a` exactly matched reviewed local commit `e097b78`
- CI: ForgeOps CI run `35136846722` completed successfully on the published documentation follow-up
- Live acceptance: exact published commit `2b8d106` and tree `dd8e51a` verified; package `0.3.0` installed; schema and field order parsed; all 33 checks passed with five explicit HTTP checks, verified redaction, overall `PASS`, and exit code `0`
- Acceptance artifact: collected at `2026-09-16T19:00:51Z` with SHA-256 `8d4d67f585a4c6b1e8f3cedb4a08f5583b06a9ab6e6b82697db62435f356dc16`
- Live safety: the accepted command used only the existing bounded Kubernetes reads and five explicit HTTP GETs; no cluster mutation occurred
- PR readiness and merge: PR #31 was marked ready only after offline validation, successful CI, exact-tree verification, and read-only live JSON acceptance passed; implementation head `103bc2f` merged at `4715628c8ef1f498bd545e8be47393be9b310c59`
- Merge integrity: implementation head and merge commit both resolve to tree `3dc1bade0004ce2a901cdab8bf48d564787acb79`
- Post-merge checks: the operator confirmed all Actions displayed by GitHub were green; the connected GitHub API exposed no workflow-run or commit-status records for the merge commit
- Closeout and cleanup: closeout PR #32 merged at `66bae40`; Gate 10 completed and both Milestone 046 branches were removed locally and remotely
- Runtime impact: none during local implementation; no package registry, image, manifest, deployment, Wiki, network, or cluster action
- Milestone 047: deterministic offline evidence validation is complete and merged through PR #33 at `a92b4b8e8593d0bffd0af1c7db800a16efd84663`
- Interface: `forgeops evidence validate --input <explicit-file>` reads one explicit regular file and returns validator success independently from the artifact's contained health result
- Validation boundary: 1 MiB, UTF-8 JSON, duplicate-key rejection, exact `forgeops.snapshot/v1alpha1` fields and values, timestamp and unique-check validation, and recalculated summary counts, overall status, and contained exit code
- Offline safety: no kubeconfig, kubectl, HTTP, network, collection, artifact rewrite, persistence, comparison, recommendation, AI reasoning, or mutation
- Local validation: 48 focused ForgeOps tests and all 106 repository tests pass
- Publication: final PR head `21c2bbaa0448027406a295380f17a88a5cf06885` has exact tree `81fc5e9d9740c6d964fed34adcc00ec58f05395b`, matching the reviewed local tree
- CI: final-head ForgeOps CI run `35155377618` and Kubernetes Manifest Validation run `35155377675` completed successfully
- Merge integrity: merge commit `a92b4b8e8593d0bffd0af1c7db800a16efd84663` resolves to the same accepted tree `81fc5e9d9740c6d964fed34adcc00ec58f05395b`
- Gate disposition: package/image release, deployment, and live acceptance were explicitly closed as not applicable; acceptance was intentionally offline
- Local package metadata: `0.4.0`; no registry package, image, tag, manifest, deployment, cluster access, live acceptance, or Wiki change
- Milestone 047 closeout and cleanup: closeout PR #34 merged at `2ebaa902f56f6b143009c4e630ba95f4a03759d8`; Gate 10 completed and both Milestone 047 branches were removed locally and remotely
- Milestone 048: deterministic offline evidence comparison is complete, merged, closed, and cleaned up
- Comparison interface: `forgeops evidence compare --before <file> --after <file>` validates both artifacts before comparing them
- Comparison semantics: checks are matched by ID; additions, removals, status transitions, and same-status evidence changes are reported in stable order while collection timestamps are ignored as differences
- Comparison exits: `0` equivalent, `1` different, and `2` invalid input or chronology; exit `1` is not a contained-health result
- Comparison safety: two explicit files only, each bounded by the existing 1 MiB validator; no kubeconfig, kubectl, HTTP, network, collection, retention, replay, diagnosis, recommendation, AI reasoning, or mutation
- Local validation: all 57 focused ForgeOps tests and all 115 repository tests pass; isolated installation and all four installed command entry checks pass
- Local package metadata: Milestone 048 advances the repository-local distribution to `0.5.0`; no distribution is published
- Publication: draft PR #35 opened from remote commit `40d461f746b27a27e0b42ccb4510ae2459c246fe`; its tree `3e88f927201f2799ff13f9a9291fcee822bfeba5` exactly matches reviewed local implementation commit `01e69896cefbd415c6b60e74683d7b2e2116493f`
- CI: ForgeOps CI run `35160149810` completed successfully on the published implementation tree
- Final publication: head `002b48ec55c6dd2cd4c8cfece0d45a2ec36f5658` and reviewed local publication commit `94e6e8fc212e888479b9fb9d482329bf1a682a7d` resolve to tree `72c23057a43b485759072e0f5876495b73124b2c`; final-head ForgeOps CI run `35160350679` passed
- PR readiness and merge: PR #35 was marked ready after separate approval and merged at `ad05786e1d94660d75e1724e4e8db6d3af7dc088`
- Merge integrity: the final published head and merge commit resolve to exact accepted tree `72c23057a43b485759072e0f5876495b73124b2c`
- Post-merge checks: the operator confirmed all Actions displayed by GitHub were green
- Gate disposition: package/image release, deployment, and live acceptance were explicitly closed as not applicable; no cluster or endpoint access occurred
- Closeout and cleanup: closeout PR #36 merged at `9055ef8d564809dd355f8cdfa175259c5b9ee677`; Gate 10 completed and both Milestone 048 branches were deleted locally and remotely
- Milestone 049: deterministic `forgeops.comparison/v1alpha1` JSON rendering is complete, merged, closed, and cleaned up
- Interface: `forgeops evidence compare --before <file> --after <file> --format text|json`; text remains the default
- JSON boundary: immutable comparison data only, with fixed order, deterministic counts, ordered deltas, explicit nulls, and no artifact paths or underlying evidence values
- Safety boundary: renderer-only authority; no new file loading, collection, subprocess, HTTP, network, persistence, diagnosis, recommendation, AI reasoning, or mutation
- Local validation: all 64 focused ForgeOps tests and all 122 repository tests pass; isolated installation, package version, all installed command entry checks, equivalent JSON comparison, manifest validation, and whitespace validation pass
- Local package metadata: Milestone 049 advances the repository-local distribution to `0.6.0`; no distribution is published
- Publication: draft PR #37 opened from remote commit `c1501c4f3834c59d010b9ee1c68190c4b490947d`; its tree `80f08b91f755d9fc97a24a3dcd64f56c413cdb58` exactly matches accepted local implementation commit `b35ffaeebde90421ea12274649baca2f2770f95d`
- CI: ForgeOps CI run `35227321405` completed successfully on the published implementation tree
- Gate 4 disposition: package/image release is explicitly closed as not applicable; version `0.6.0` remains repository-local metadata and no distribution, image, or release tag was published
- Gate 5 disposition: deployment is explicitly closed as not applicable; no deployable artifact, manifest, workload, ServiceAccount, RBAC, configuration, rollout, restart, or persistent state changed
- Gate 6 disposition: live acceptance is explicitly closed as not applicable; deterministic acceptance is intentionally offline and no SignalForge, Kubernetes API, or application endpoint was accessed
- Final publication: head `a607126b0e2f38730a1ec6f383c72681523a11fb` resolves to accepted tree `253fdc4f34756d930bbfa77a583c125eb6600dd9`; final-head ForgeOps CI run `35229392947` passed
- PR readiness and merge: PR #37 was marked ready after final-head CI and exact-tree verification, then merged at `972e6115e507894f9f2b916bb5f655365d99a2fb`
- Merge integrity: the final published head and merge commit resolve to exact accepted tree `253fdc4f34756d930bbfa77a583c125eb6600dd9`
- Runtime impact: none; no registry artifact, image, release tag, manifest, deployment, cluster access, application endpoint access, persistent-state change, or Wiki change occurred
- Closeout and cleanup: closeout PR #38 merged at `38bf1d84d5ad0611d050e1825233af82f369b4af`; Gate 10 completed and both Milestone 049 branches were deleted locally and remotely
- Milestone 050: bounded synthetic ForgeOps scenario corpus implemented locally on `codex/milestone-050-forgeops-scenario-corpus`
- Corpus: five focused before/after pairs cover timestamp-only stability, a Pod-restart warning, a routing regression, incomplete evidence, and routing recovery
- Contract reuse: every input uses `forgeops.snapshot/v1alpha1`; every expected result is exact `forgeops.comparison/v1alpha1` output from the unchanged validation and comparison seams
- Semantic coverage: stable evidence returns comparison exit `0`; regressions and recovery return comparison exit `1`; incomplete evidence retains contained `UNKNOWN` and exit `2` independently from comparison exit `1`
- Scenario boundary: synthetic evaluation data only, with one isolated check per artifact; not captured evidence, complete cluster health, training data, provenance, diagnosis, or recommendation
- Authority boundary: no production model, schema, CLI, package-version, collection, subprocess, HTTP, network, persistence, AI reasoning, remediation, or mutation change
- Local validation: all 68 focused ForgeOps tests and all 126 repository tests pass; isolated installation, package version, all installed command entry checks, stable and recovery comparisons, manifest validation, and whitespace validation pass
- Publication: draft PR #39 opened from remote commit `067af70ef568a7342a8af6218cb6cddd252d9894`; its tree `53f6de423608b1f6ca3a74b93b04b65f93d67051` exactly matched accepted local implementation commit `099cdbc59b95d81c9eadfa78e21f0ade5974d88d`
- CI: ForgeOps CI run `35240317432` completed successfully on the published implementation tree
- Gate disposition: package/image release, deployment, and live acceptance were explicitly closed as not applicable; acceptance remained entirely offline
- PR readiness and merge: PR #39 was marked ready under Gate 7 and merged under Gate 8 at `090a47f7cd546f4d2c0dac952da387f4e1fdf863`
- Merge integrity: the published head and merge commit resolve to exact accepted tree `53f6de423608b1f6ca3a74b93b04b65f93d67051`
- Closeout and cleanup: documentation-only PR #40 merged at `59cad31d28eee0d41e345a105b306f5165444cd5`; Gate 10 removed both Milestone 050 branches locally and remotely, and clean `main` was synchronized at that commit
- Runtime impact: none; no registry artifact, image, release tag, manifest, deployment, cluster access, application endpoint access, persistent-state change, or Wiki change occurred
- Milestone 051: trustworthy execution provenance is implemented and validated locally on `codex/milestone-051-forgeops-execution-provenance`
- Interface: `forgeops provenance` reports distribution, source-project, and module versions, loaded module path, Python executable, execution mode, install source, status, and findings
- Execution modes: isolated normal installation for operator use; repository-owned source launcher for current-checkout development
- Detection: version disagreement and invalid/missing sources fail; temporary-directory editable sources warn
- Documentation: one current operator and learning guide consolidates architecture, commands, evidence flow, exit domains, recovery, and trust boundaries while historical milestone documents remain intact
- Package metadata: repository-local version advances to `0.7.0`; no distribution is published
- Local validation: all 79 focused ForgeOps tests and all 137 repository tests pass; isolated install, installed command entries, source launcher, Python compilation, manifest validation, and whitespace validation pass
- Authority boundary: local Python/package metadata only; no kubeconfig, kubectl, HTTP, evidence loading, network, deployment, cluster access, or mutation
- Publication: draft PR #41 opened from published implementation commit `8dc35c862e4c6a30e59af2c33d4512757c82772c`; its tree `621d1cfbc0faf8257a4711f6b6747172694a7ed7` exactly matches accepted local implementation commit `7443a278fc638458a036ed5251e7d1aa7e29903c`
- Gate disposition: package/image release, deployment, and live acceptance were explicitly closed as not applicable; no registry, image, release tag, deployment, cluster, or endpoint action occurred
- Final publication: head `4e5e7334448fb734fdc7e1f869d7215c8855c4cc` resolves to accepted tree `652d01fdb7933e037b0097170610ea8480164588`; final-head ForgeOps CI run `35265922723` passed
- PR readiness and merge: PR #41 was marked ready under Gate 7 and merged under Gate 8 at `e5e2a0898480e7722295e8df5e35eb25d4829848`
- Merge integrity: the implementation merge commit resolves to exact accepted tree `652d01fdb7933e037b0097170610ea8480164588`
- Closeout and cleanup: PR #42 merged at `fd8187697dc472e2d3c39f2202636412a551b728`; both Milestone 051 branches were deleted locally and remotely, and clean `main` was synchronized at that commit
- Milestone 052: deterministic exact-byte evidence integrity records are implemented and merged through PR #43
- Interface: `forgeops evidence integrity create --input <file>` and `forgeops evidence integrity verify --input <file> --record <file>`
- Integrity contract: strict `forgeops.integrity/v1alpha1` JSON with evidence schema, collection timestamp, context, SHA-256 digest, byte length, and explicit limitations
- Verification semantics: exit `0` match, `1` mismatch, and `2` invalid/unreadable evidence or record; these are separate from contained health, validation, and comparison exits
- Trust boundary: exact-byte change detection relative to a separately retained trusted record; no authorship, authenticity, signature, attestation, trusted time, or chain-of-custody claim
- Authority boundary: explicit local bounded files only; no kubeconfig, kubectl, HTTP, network, collection, retention automation, replay, diagnosis, recommendation, AI reasoning, or mutation
- Package metadata: repository-local version advances to `0.8.0`; no distribution is published
- Local validation: all 87 focused ForgeOps tests and all 145 repository tests pass; isolated non-editable `0.8.0` installation, installed command entries, source launcher, Python compilation, manifest validation, and whitespace validation pass
- Publication: remote implementation commit `912468e566086a5234339ac09b3f98dddc53b4a2` resolves to tree `eeb97ba2a7442353116cef90f9d77df180b02c48`, exactly matching accepted local commit `181a8d762925f2620595f03ad927424cd5f06ac1`
- CI: ForgeOps CI run `35288211586` completed successfully on the exact published tree
- PR readiness and merge: draft PR #43 was marked ready after CI and exact-tree verification, then merged at `b4f42c24cb3afd3b4420716038d508a9f60712c3`
- Merge integrity: the merge commit resolves to exact accepted tree `eeb97ba2a7442353116cef90f9d77df180b02c48`
- Gate disposition: package/image release, deployment, and live acceptance were closed as not applicable; no registry, image, release tag, cluster, endpoint, persistent-state, or Wiki action occurred
- Closeout and cleanup: PR #44 merged at `801f8cedaf411361e3e02b47cdae217ee56959c5`; both Milestone 052 branches were deleted locally and remotely, and clean `main` was synchronized at that commit
- Milestone 053: bounded offline scenario replay is implemented and merged through PR #45
- Interface: `forgeops scenario replay --before <file> --after <file> --expected <file>` requires three explicit local files
- Expected-comparison boundary: strict `forgeops.comparison/v1alpha1` loading with a 256 KiB limit, duplicate-key rejection, exact ordered fields, supported statuses and kinds, sorted unique deltas, kind-specific shapes, and recalculated counts
- Replay semantics: exit `0` expectation match, `1` valid mismatch, and `2` invalid evidence, expected comparison, or chronology; replay success is independent of contained health and comparison exit
- Scenario authority: no directory discovery, collection, kubeconfig, kubectl, HTTP, network, retention, integrity claim, runbook mapping, diagnosis, recommendation, AI reasoning, remediation, or mutation
- Package metadata: repository-local version advances to `0.9.0`; no distribution is published
- Local validation: all 95 focused ForgeOps tests and all 153 repository tests pass; isolated non-editable `0.9.0` installation, installed command entries, source launcher, Python compilation, manifest validation, whitespace validation, and stable/recovery/incomplete-evidence replay checks pass
- Publication: remote implementation commit `500bc4da028b94b2ad403f401a7777c3e0e79f41` resolves to tree `ddfa67a59024947c7403a679ce7254cdb1e232a3`, exactly matching accepted local commit `26538bac2d09e2fb9aef35f6032d71bcf109233a`
- CI: ForgeOps CI run `35295260302` completed successfully on the exact published tree
- PR readiness and merge: draft PR #45 was marked ready after CI and exact-tree verification, then merged at `6900aa956786976fb7a20e967137a8a3096e4514`
- Merge integrity: the implementation merge commit resolves to exact accepted tree `ddfa67a59024947c7403a679ce7254cdb1e232a3`
- Gate disposition: package/image release, deployment, and live acceptance were closed as not applicable; no registry, image, release tag, cluster, endpoint, persistent-state, or Wiki action occurred
- Closeout and cleanup: documentation-only PR #46 merged at `c8ad7b6e8a7e740521446cb23a039b71f09f82d1`; Gate 10 removed both Milestone 053 branches locally and remotely, and clean `main` was synchronized at that commit
- Milestone 057: strict `forgeops.runbook-mapping/v1alpha1` loading and `forgeops runbook mapping validate` are complete and merged through PR #54 at `35c6e87c936eb6d486750aed40aa398039164e62`; validation exit remains separate from contained mapping completeness
- Milestone 058: deterministic `forgeops incident brief` JSON output is complete and merged through PR #55 at `67d0d41fbb15a561b428d154d93465272c566aa7`; every fact is cited from the supplied comparison and every runbook is a grounded catalog-rule match rather than a diagnosis
- Milestone 059: exact incident-brief replay across five synthetic scenarios is complete and merged through PR #56 at `e2c313494b051508c1c7ee375792e8d00eec52a9`; replay exit reports expectation equality rather than contained state
- Milestone 060: deterministic operator text rendering is complete and merged through PR #57 at `f3c63bacfcfdca4e55cfb9eb8adfe1b70d110921`; text and JSON retain identical facts, uncertainty, informational guidance, and authority limitations
- Milestone 061: nine-case adversarial evaluation and the model-readiness decision are complete and merged through PR #58 at `9f3d8f13f3a0fe3b746084c889848d19f0ad431c`; ForgeOps CI runs `35448696493`, `35449046318`, `35449474657`, `35449756167`, and `35450511724` passed for Milestones 057-061
- Readiness decision: deterministic briefing is ready for a separately gated read-only end-to-end demonstration; model and retrieval integration remain deferred until measured unmet operator need and explicit privacy, quality, and failure-mode criteria exist
- Authority boundary: Milestones 057-061 added no package publication, model, retrieval service, external service, live incident claim, cluster access, endpoint access, deployment, recommendation authority, remediation authority, persistent state, or mutation
- Closeout and cleanup: grouped documentation-only PR #59 merged at `28c02293301fe7380d98485a0717ecc68e8069f8` and recorded final acceptance; Gate 10 removed all Milestone 057-061 and previously retained historical branches locally and remotely, leaving clean synchronized `main` as the only branch
- Milestone 062: deterministic incident-copilot demonstration approved with all ten gates; the offline routing-regression rehearsal passed through provenance, evidence validation, comparison, catalog validation, mapping validation, text and JSON briefing, and exact brief replay
- Live acceptance: two 33-check `PASS` snapshots across `2026-09-19T18:08:08Z` through `2026-09-19T18:09:32Z` strictly validated and matched their immediate integrity records; comparison found zero changed checks; mapping contained zero deltas; and JSON and text briefs both rendered `STABLE` with `point-in-time-only` uncertainty
- Operator assessment: no concrete operator question remained unanswered by the deterministic brief, so model and retrieval integration remain deferred
- Demonstration boundary: synthetic `DEGRADED` behavior remains explicitly separate from the live `STABLE` baseline; no failure was injected and no live artifact was committed or published
- Authority boundary: no new command, schema, package version, dependency, model, retrieval service, broader collection, deployment, recommendation, remediation, or mutation is introduced
- Publication and merge: accepted implementation head `b7969d888f9ca032c9a7969af3783d154e565ae2` resolved to exact tree `18894b421b35d9c2d959946f15448396140fe454`; PR #63 was marked ready and squash-merged at `6e7e5802037fa55245761410196f165281a4c804`

## Milestone 038 closeout

- Release: `0.6.0`
- Source acceptance: 58 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, AMD64/ARM64 non-publishing build, repository validation, whitespace validation, Windows build, and local browser interactions passed
- Behavior: valid formatting changes require explicit Apply or Cancel; invalid YAML remains unchanged and routes to Validation
- Release acceptance: the AMD64/ARM64 OCI index was independently digest-verified, deployed after an approved Deployment-only diff, and passed runtime, HTTP, security-header, and live browser validation

## Completed milestones

- 001-009: Cluster foundation and initial Restaurant API workload
- 010: Restaurant API CI
- 011: Automated Docker build
- 012: Versioned release `0.5.0`
- 013: Kubernetes manifests under version control
- 014: Laptop `kubectl` access
- 015: Deployment helper and smoke test
- 016: SignalForge operator command helper
- 017: Operator runbook
- 018: Kubernetes manifest validation in CI
- 019: Developer command layer
- 020: Basic application observability with `/metrics`
- 021: Metrics collection planning
- 022: Lightweight Prometheus metrics collection
- 023: Application metrics refinement
- 024: Kubernetes Metrics Server evaluation and secure kubelet PKI
- 025: Persistent Prometheus storage planning
- 026: Persistent Prometheus storage implementation and recovery validation
- 027: Lightweight Grafana design and dashboard requirements accepted
- 028: Lightweight Grafana implementation, persistence and recovery validation
- 029: Limited alerting design accepted and merged
- 030: Limited alerting rules validated, activated and verified without notification delivery
- 032: Forge YAML Workbench `0.1.1` built, published, hardened, deployed and browser-validated
- 033: Workbench usability improved; `0.1.2` published, digest-pinned, deployed and live browser-validated
- 034: Workbench deterministic Kubernetes checks and actionable remediation released as `0.2.0`, deployed, accepted, and merged
- 035: General YAML inspection released as `0.3.0`, deployed, live browser-accepted, and merged
- 036: corrected `0.4.1` published, digest-pinned, deployed, live browser-accepted, and merged through PR #13 at `fc16ad1`
- 037: pinned OWASP Kubernetes Top 10:2025 review profile and corrected finding navigation released as `0.5.1`, deployed, browser-accepted, and squash-merged through PR #14 at `dd46a08`
- 038: browser-local formatting preview released as `0.6.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #16 at `4fed28c`
- 039: browser-local Markdown reports released as immutable `0.7.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #18 at `1e0c525`
- 040: Validation result filters released as immutable `0.8.0`, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #20 at `6fa5092`
- 041: browser-local YAML Tree search released as immutable `0.9.0`, deployed, accepted, merged through PR #22 at `0f3d44e`, and cleaned up
- 042: safe browser-local YAML file drop released as immutable `0.10.0`, deployed, accepted, and merged through PR #23 at `020d5e7`
- 043: curated repository-owned GitHub Wiki front door published, browser-accepted, merged, and cleaned up; documentation-only Restaurant API image publication is suppressed

## Latest release milestone

- 042: safe browser-local one-file YAML drop with visible and accessible target states, shared unsaved-change protection, deterministic state boundaries, and keyboard-equivalent opening
- Trust boundary: browser-provided basename and contents remain in memory; no upload, backend, persistence, telemetry, cluster credentials, Kubernetes API access, or automatic remediation
- Verification: 92 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, repository validation, whitespace checks, Windows validation, CI, AMD64/ARM64 builds, and source and live browser reviews passed
- Publication and deployment: immutable AMD64/ARM64 `0.10.0` is live at OCI index `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`
- Runtime acceptance: generation 14, one Ready Pod on `forge-node-03`, zero restarts, exact configured/runtime digest match, one ready endpoint at `10.244.54.203:8080`, fresh HTTP 200 responses, expected security headers, and the complete file-drop workflow passed
- Completion record: release and acceptance evidence merged through PR #23 at `020d5e7`; post-merge branch cleanup is complete

## Previous completed milestone

- 040: counted Validation result filters with level isolation, empty-section handling, edit-time recomputation, reset boundaries, and complete-report isolation
- Trust boundary: ephemeral browser-local presentation state; no backend, persistence, telemetry, cluster credentials, Kubernetes API access, or automatic remediation
- Verification: 74 tests, validator reproducibility, production build, CSP scan, zero-vulnerability audit, repository validation, whitespace checks, Windows validation, CI, AMD64/ARM64 build, and source and live browser reviews passed
- Publication and deployment: immutable AMD64/ARM64 `0.8.0` was released at OCI index `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`
- Completion: PR #20 merged at `6fa5092`; Workbench CI run 142, Kubernetes Manifest Validation run 124, and Restaurant API Docker Build run 57 passed on `main`

## Current observability state

- Prometheus namespace: `forge-observability`
- One Prometheus replica
- Image: `prom/prometheus:v3.13.2`
- Pod discovery restricted to `forge-restaurant`
- RBAC restricted to get, list, and watch Pods
- Scrape interval: 30 seconds
- Retention: 30 days or 24 GB
- Storage: 30 GiB retained local PV on the head NVMe
- Access: ClusterIP plus `kubectl port-forward`
- Healthy Restaurant API targets: 3
- Prometheus Pod: stable with zero restarts after rollout
- Automatic target rediscovery: confirmed through application Pod replacement
- Request-duration histogram: available across all three application Pods
- Traffic classification: `application` and `synthetic`
- Cardinality protection: unmatched URLs use `path="unmatched"`
- Baseline queries: `docs/observability/prometheus-queries.md`
- Alert evaluator: two Restaurant API scrape-coverage rules loaded by Prometheus
- Alert state at acceptance: both rules `health=ok` and `state=inactive`
- Trial delays: five-minute warning and two-minute critical, still provisional operational thresholds
- Alert delivery: none; no Alertmanager or receiver is configured
- Alert rollback: validated baseline ConfigMap retained off-cluster with SHA-256 recorded in Milestone 030

## Current Grafana state

- Namespace: `forge-observability`
- Deployment: `grafana`
- Replicas: 1
- Grafana OSS version: `13.2.1`
- Image: `grafana/grafana:13.2.1@sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283`
- Access: ClusterIP plus authenticated `kubectl port-forward`; anonymous dashboard access is rejected
- Storage: 3 GiB retained local PV `grafana-local-nvme` on the `forge-head` NVMe
- Filesystem UUID: `a506c674-127a-46da-9c7d-d158b6d1bb75`
- Mount: `/mnt/signalforge-grafana`
- Dashboards: SignalForge Restaurant Overview and SignalForge Scrape Diagnostics
- Dashboard panels: 12 total, with provisioned Prometheus data source and stable dashboard/data-source UIDs
- Healthy Restaurant API targets represented in dashboards: 3
- Pod replacement persistence: confirmed for database-backed personal settings
- Extended observation: zero Grafana restarts; sampled use approximately 5m CPU and 192-202 MiB memory
- Dashboard responsiveness: no load above five seconds observed during acceptance checks
- Cold backup: verified off-node with independent SHA-256 validation
- Isolated restore: passed authentication, provisioning, dashboard queries, browser rendering and persisted-setting recovery
- Restore readiness: 41 seconds
- Measured recovery time through usable validated dashboards: 262 seconds / 4.37 minutes
- Recovery objective: demonstrated inside the one-hour Grafana RTO target
- Rollback/return: passed while retaining Grafana storage and credentials and preserving Prometheus collection
- Protected recovery material: Grafana admin username, password and encryption `secret-key` stored independently in the password manager
- Backup cadence: weekly and before upgrades when appropriate; four successful weekly archives retained manually

## Current Kubernetes resource-metrics state

- Metrics Server namespace: `kube-system`
- Deployment: `metrics-server`
- Image: `registry.k8s.io/metrics-server/metrics-server:v0.9.0`
- Replicas: 1
- Metrics API: `metrics.k8s.io/v1beta1`
- Collection interval: 15 seconds
- Node address preference: `InternalIP,ExternalIP,Hostname`
- Kubelet TLS: verified with the Kubernetes service-account CA
- Insecure kubelet TLS flag: not used
- Kubelet serving certificates: Kubernetes-CA-signed with hostname and InternalIP SANs
- Live node coverage: 4 of 4 nodes
- Observed Metrics Server footprint: 4m CPU and 21 MiB memory
- `kubectl top nodes` and `kubectl top pods`: available

## Persistent-storage implementation

Milestone 025 selected the following Prometheus storage target:

- Dedicated 32 GiB ext4 partition on the verified `forge-head` Samsung SSD 950 PRO 512GB NVMe
- Static 30 GiB Kubernetes `local` PV and PVC
- Non-default `signalforge-local-nvme` StorageClass with `WaitForFirstConsumer`
- `ReadWriteOnce` access, `Retain` reclaim policy, and exact `forge-head` PV node affinity
- One Prometheus replica using the `Recreate` strategy
- Retention of 30 days or 24 GB, whichever is reached first
- Weekly cold backups copied off `forge-head`, with the four newest retained
- Recovery objectives of RPO at or below 7 days and RTO at or below 1 hour
- Existing ClusterIP and `kubectl port-forward` access model preserved

Milestone 026 host preparation is complete:

- Verified `/dev/nvme0n1` as Samsung SSD 950 PRO 512GB, serial `S2GMNCAGB06236R`
- Backed up the prior partition table before the explicitly approved disk erase
- Completed a destructive four-pattern write/read test of the new 32 GiB partition with zero bad blocks
- Confirmed the NVMe media-error count remained 215 before and after that test
- Created ext4 filesystem UUID `4f2feee5-72a7-4f32-a351-b4253c4a0854`
- Mounted the filesystem by UUID at `/mnt/signalforge-prometheus`
- Created `data` as `65534:65534` with mode `0750` and verified writes as that identity
- Proved the data path disappears when the NVMe is unmounted, preventing silent SD-card fallback writes

The NVMe cutover is live. Pod-replacement persistence and six-block off-node backup/restore validation passed. See Milestone 026 for the checksum and evidence.

## Immediate next step

Maintain the accepted ForgeOps v1.0.0 baseline. Any future milestone must
directly improve the final incident-copilot demonstration, prove that it is
trustworthy, or prepare a future release; work that satisfies none of those
purposes remains deferred. The release channel is a GitHub Release wheel with
SHA-256 checksums, not PyPI, and the public reuse license is MIT. The accepted
demonstration identified no concrete unmet operator question, so model and
retrieval integration remain deferred.

The [ForgeOps post-v1 improvement roadmap](roadmaps/forgeops-post-v1-roadmap.md)
proposes a separately gated sequence for installed-artifact demonstration,
trust-failure evaluation, cross-platform release acceptance, evidence-bundle
and release-provenance decisions, a conditional v1.1 path, deterministic v2
profiles and timelines, and an evidence-gated assistive v3 horizon. The roadmap
authorizes no implementation, live access, model integration, release, or
remediation action by itself.

Milestones 054-061 are complete, merged, synchronized, and cleaned up. The
Milestone 057-061 implementation PRs are #54-#58; grouped closeout PR #59
records final acceptance and Gate 10 cleanup. All milestone and previously
retained historical branches were deleted locally and remotely.

Milestone 062 planning, offline rehearsal, live read-only acceptance, PR
readiness, merge, documentation-only closeout, and branch cleanup are complete.
Implementation PR #63 merged at `6e7e580`; closeout PR #64 merged at
`5619a5f`. The operator synchronized clean local `main`, removed the local
implementation branch (no local closeout branch existed), removed both remote
milestone branches, pruned stale remote-tracking references, and removed the
temporary demonstration artifacts. The live demonstration used only the
existing bounded reads from the operator workstation; no runtime, deployment,
persistent state, or cluster object changed.

Milestone 063's read-only audit built the current pure-Python wheel, installed
it into a fresh Python 3.12 environment without a registry, and passed installed
provenance, console and module help, strict evidence validation, and stable
scenario replay. It also confirmed seven release blockers: product and
distribution identity, `1.0.0` version alignment, exact artifact validation,
supported-Python proof, MIT license metadata, bounded GitHub release automation,
and an operator release procedure. No live system or external service was used.
The accepted assessment tree `d407063392c9294fc8aed27a747744ee1c111201`
was published at head `25b9340b56b58af7fd8f88fdffcf82d1ed7ed5e9`
and squash-merged through PR #66 at
`2293865859ddc6259f8cedee95705e800a152bc6`.
Closeout PR #67 merged at
`1721503cc6a3e4249654bffc14d89daf82f95dda`; the operator synchronized clean
`main`, deleted both Milestone 063 remote branches, pruned, and verified that
only local and remote `main` remained.

Milestone 064 has completed local implementation and validation for only those
seven blockers. Its candidate uses
the `signalforge-forgeops` identity and version `1.0.0`, the MIT license, an
exact reproducible wheel plus SHA-256 record, Python 3.11-3.14 source and wheel
matrices, bounded tag-only GitHub Release automation, and an operator release
procedure. PR #68, both nine-job Python 3.11-3.14 CI runs, reproducible artifact
digest verification, and fresh Windows Python 3.14.7 offline acceptance passed.
PR #68 squash-merged at `0fde4d904b9731a3c99f0ae5d367ac8f36a1fce1`.
Closeout PR #69 merged at `9f86d2ceefd40e58282190711ec5e2eb69adba6f`;
clean `main` synchronization, both branch deletions, and temporary candidate
removal completed Gate 10. Milestone 064 published no package or tag.

Milestone 065 reconfirmed the exact accepted source and wheel before creating
annotated tag `forgeops-v1.0.0` at the Milestone 064 closeout commit. Release
workflow run `35465207955` passed all ten tagged-source, reproducible-build,
exact-wheel install, and publication jobs. The final GitHub Release contains
only the 51,589-byte wheel and checksum file. Fresh Windows Python 3.14.7
acceptance verified both published asset digests, installed with `--no-index`,
returned provenance `OK`, and passed the offline command smoke path. Release
record PR #70 merged at `1369df1a4fec39bcce781ef814274bee435c4644`.
Documentation-only closeout PR #71 merged at
`8a671c9d186ce37321fa925e6e957ac9e1286507`. The operator synchronized clean
`main` at that commit, removed both Milestone 065 branches locally and
remotely, pruned remote references, and removed the temporary acceptance
directory. Final verification preserved the non-draft, non-prerelease GitHub
Release and immutable tag at the accepted source commit. ForgeOps v1.0.0 is
fully closed without changing the release assets, package inputs, live system,
or remediation authority.

## Supporting completed work

Lightweight Grafana remains deployed with retained storage, provisioned SignalForge dashboards, tested persistence, encrypted off-node backup, isolated restore, credential recovery and rollback/return.

The Milestone 029 [limited-alerting design](observability/limited-alerting-specification.md) was accepted by Mike and merged through PR #4 at `1837868` on 2026-09-10. It covers reduced scrape coverage and no-healthy-target conditions using the manual three-replica baseline. Five-minute and two-minute delays remain provisional, not measured operational thresholds. Performance alerts, notification channels, Alertmanager, and broader monitoring coverage remain deferred.

[Milestone 030](milestones/milestone-030-limited-alerting-implementation.md) is complete. Its offline package merged through PR #5 at `604e38e` after real promtool 3.13.2 passed both rules and all 19 scenarios. The guarded activation candidate merged through PR #6 at `f54b961`. After explicit approval on 2026-09-11, only the Prometheus ConfigMap changed and only Prometheus restarted. Immediate and independent checks confirmed three healthy targets, an exact live/repository configuration match, and both accepted rules loaded, healthy and inactive. A checksum-recorded baseline recovery file is retained. No Alertmanager, receiver or notification delivery exists.

`Milestone 032` is complete and merged through PR #8 at `3b6bac5`.

`Milestone 033` is complete and merged through PR #9 at `7aadedd`. Forge YAML Workbench `0.1.2` runs as one Ready replica with zero restarts from the pinned OCI index digest. NodePort routing, `/healthz`, the application page, security headers, sample loading, format feedback, editing state, the format shortcut, and YAML download all passed live verification.

Milestone 034 published, immutably pinned, deployed, and live browser-validated the approved `0.2.0` AMD64/ARM64 image, then merged through PR #10 at `9848618`. The running Pod is Ready with zero restarts and its runtime ImageID matches the reviewed OCI index digest.

Milestone 035 published and deployed its separately approved `0.3.0` AMD64/ARM64 image at OCI index digest `sha256:3abd4292f6cbd506dbc976924d2b61cf8093a7653e02654efaedc207e3f3086f`. It adds an explicit General YAML mode alongside the default Kubernetes mode. Both modes share browser-local parsing, formatting, parser diagnostics, file handling, and tree navigation. General YAML accepts mappings, sequences, and scalars while omitting Kubernetes-only findings. The Deployment-only rollout completed with one Ready replica, zero restarts, a matching runtime ImageID, ready routing, HTTP 200 responses, both mode markers, and the expected security headers. Live browser interaction acceptance passed, and PR #11 merged at `b45ee0b`.

Continue observing naturally occurring alert behavior without injecting a failure merely to produce firing evidence.

## Known temporary limitation

Prometheus and Grafana remain dependent on `forge-head` and its local NVMe during head-node or device failure. Weekly off-node backups remain manual. Grafana service recovery from an accepted backup was measured at 4.37 minutes on a functioning cluster, but full head-node or NVMe reconstruction remains outside that result. Prometheus full service-restoration timing remains a separate limitation.

Kubelet serving-certificate rotation can create new pending CSRs. Core Kubernetes does not automatically approve these serving requests, so an operator must validate the requester, signer, usages, subject, and SAN ownership before approval.

Forge YAML Workbench `0.10.0` is deployed from the published AMD64/ARM64 OCI index at `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`. Its runtime, safe YAML file drop, Tree search, formatting preview, Markdown report workflow, Validation filters, OWASP profile, schema boundaries, General YAML isolation, strict headers, and corrected finding-link scrolling passed live acceptance. NodePort `30081` remains private-lab HTTP exposure.
