# Milestone 042 — Safe browser-local YAML file drop

**Status:** Release published and immutable Deployment candidate prepared; cluster deployment not authorized
**Started:** 2026-09-15
**Branch:** `codex/milestone-042-safe-yaml-drop`
**Baseline:** `main` at `0f3d44e2abff204f0019ea6d97bb2ab4b1ffe198`
**Candidate release:** `0.10.0`

## Goal

Make local YAML files easier to open by adding a visible editor drop target while preserving the Workbench's browser-only trust boundary and protecting unsaved work.

## Approved scope

- Accept exactly one local file whose basename ends in `.yaml` or `.yml`, case-insensitively.
- Identify the editor as the drop target with persistent instructions and a visible drop-ready state.
- Read accepted contents with the browser File API and use the existing input-replacement path.
- Preserve the accepted basename for YAML and Markdown downloads.
- Share one unsaved-change confirmation boundary across dropped-file, Open file, and sample replacement.
- Prevent a file dropped elsewhere on the page from navigating the browser or replacing YAML.
- Report success, cancellation, unsupported types, multiple or missing files, misplaced drops, and read failures through the existing live action status.
- Preserve the inspection mode and active tab after replacement while resetting the Validation filter and Tree search and invalidating a prepared report.
- Keep YAML and all derived state unchanged when replacement is cancelled, rejected, or unreadable.

## Interaction and accessibility

- A persistent visible hint identifies accepted extensions and the Open file alternative.
- File drag-over adds text and a dashed boundary, so the active target is not communicated by color alone.
- Open file and Ctrl+O or Cmd+O remain complete keyboard-accessible equivalents.
- The editor references its instructions with `aria-describedby`.
- Existing polite live status announces drop outcomes.
- Escape, drag leave, drag end, window blur, and drop remove transient drop presentation.
- A successful drop focuses the editor; native confirmation remains keyboard operable.
- Non-file drags remain inert and do not interfere with text interaction.

## State boundaries

| Event | YAML and filename | Mode and tab | Validation filter | Tree search | Prepared report |
| --- | --- | --- | --- | --- | --- |
| Accepted replacement | Replaced; new clean snapshot | Preserved | Reset to All | Reset | Invalidated |
| Cancelled dirty replacement | Preserved | Preserved | Preserved | Preserved | Preserved |
| Rejected, multiple, or unreadable file | Preserved | Preserved | Preserved | Preserved | Preserved |
| Drag enter, leave, Escape, drag end, or blur | Preserved | Preserved | Preserved | Preserved | Preserved |
| Accepted invalid YAML | Replaced and clean | Preserved | Reset to All | Reset | Invalidated; Validation reports the parser error |

No drag state or file contents survive a page refresh.

## Trust boundary

Only the browser-provided basename and contents enter application memory. The Workbench does not obtain or retain the source filesystem path. It does not upload, transmit, log, cache, or persist the file or its contents.

This milestone adds no network request, backend processing, telemetry, cookie, local storage, session storage, Kubernetes credentials, API access, RBAC, deployment control, or cluster mutation. Existing clipboard and download actions remain the only export boundaries.

## Exclusions

- multiple-file, batch, directory, or folder processing
- document concatenation, merging, or append-versus-replace choices
- URL, browser-text, or remote-resource drops
- clipboard enhancements or automatic inspection-mode selection
- content-based file-type inference
- file history, recent files, persistence, or recovery
- streaming parsing, Web Workers, size limits, or large-file guarantees
- display preferences, themes, or additional report formats
- YAML repair, replacement, or automatic remediation
- backend, network, Kubernetes API, credential, or deployment controls

## Implementation state

- Added a persistent editor drop instruction and visible drop-ready overlay.
- Added file-only drag detection, case-insensitive extension eligibility, single-file enforcement, and guarded asynchronous reading.
- Added a shared dirty-source confirmation for drop, Open file, and Load sample actions.
- Added page-level navigation prevention for misplaced file drops.
- Added deterministic cleanup for leave, drop, Escape, drag end, and blur.
- Advanced application and lockfile candidate metadata to `0.10.0`.
- Corrected stale Milestone 041 merge and cleanup status and the Kubernetes README's live `0.9.0` image facts without mutating Kubernetes manifests.

## Deterministic verification

- All 92 automated tests pass across analyzer, schema, OWASP profile, formatting diff, Markdown report, Tree search, and DOM interaction suites.
- Nine focused interaction tests cover file-only drag activation, accessible instructions, cleanup boundaries, file-count and extension rejection, case-insensitive acceptance, browser-local processing, cancelled dirty replacement, shared picker/sample confirmation, read failure, successful state resets, invalid-YAML routing, focus, and misplaced-drop navigation prevention.
- Validator reproducibility passes for all 12 bundled Kubernetes resources.
- The production build completes successfully; the established bundle-size advisory remains non-blocking.
- Strict-CSP validation confirms the production JavaScript contains no eval or Function-constructor usage.
- The complete dependency audit reports zero vulnerabilities.
- Repository Kubernetes validation and all 38 supporting Grafana and Prometheus Python tests pass.
- Whitespace validation passes.
- Clean Windows validation passes from a committed-lockfile installation: all 92 tests, validator reproducibility, production build, strict-CSP scan, and the complete zero-vulnerability audit.
- Operator browser review passes the visible drop hint and overlay, successful load and focus, dirty-source cancellation and confirmation, unsupported and multiple-file rejection, misplaced-drop navigation prevention, keyboard Open file path, invalid-YAML routing, and shared replacement safeguards.
- Draft PR #23 targets unchanged `main` baseline `0f3d44e` from connector-authored commit `ba97289c391cab7e7a33f13efc2ca39103065214`; remote tree `0c72ff7b8678914338c34e566b2acf02c8592b37` exactly matches the accepted local tree.
- Workbench CI run 151, Kubernetes Manifest Validation run 130, and the non-publishing AMD64/ARM64 Docker Build run 153 pass. The guarded workflow skipped release preparation, registry login, and image publication.
- Annotated tag `forge-yaml-workbench-v0.10.0` resolves to accepted source commit `ba97289c391cab7e7a33f13efc2ca39103065214`.
- Docker Build run 154 passed the tagged publication path and published `wmstipes/signalforge-yaml-workbench:0.10.0` for AMD64 and ARM64.
- The immutable OCI index is `sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206`; active platform manifests are AMD64 `sha256:c8223d013931e0c02a582f372b826cb827eed1d6f2ba887eac7661387ef03fa2` and ARM64 `sha256:a297014f6df7579c25bcaaa6bbea12bb39e398a36828d647228e5859e7b77869`.
- After separate approval, the tracked Deployment version labels and image reference and the repository validator expectation were locally updated to immutable `0.10.0`. The live cluster remains unchanged at `0.9.0`.
- Post-mutation verification passes all 92 Workbench tests, validator reproducibility, production build, strict-CSP scan, zero-vulnerability audit, repository manifest validation, all 51 supporting Python tests, and whitespace validation.

## Gated delivery workflow

1. Planning approval — complete.
2. Local implementation — complete on the feature branch.
3. Local automated verification and source acceptance — complete, including clean Windows and operator browser review.
4. Publication — complete after separate approvals for the remote source branch, draft PR #23, release tag, and AMD64/ARM64 image.
5. Deployment-manifest mutation — local mutation complete after separate approval; publication and cluster deployment remain unapproved.
6. Cluster deployment — not authorized.
7. Live browser acceptance — not authorized.
8. Pull-request readiness — not authorized.
9. Merge — not authorized.
10. Cleanup — not authorized.
