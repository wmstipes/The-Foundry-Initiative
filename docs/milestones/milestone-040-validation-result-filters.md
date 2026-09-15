# Milestone 040 — Validation result filters

**Status:** Complete. Immutable `0.8.0` deployed, runtime-verified, live browser-accepted, and merged through PR #20
**Started:** 2026-09-14
**Completed:** 2026-09-15
**Branch:** `codex/milestone-040-validation-filters`
**Baseline:** `main` at `1a3a4ecf05f9bda5a8c6419267e80d22aa5c76c4`
**Merge:** `6fa5092210633abde28335b76dcad1e085578789`

## Goal

Make the growing Validation view easier to review by filtering its existing results by level without changing analysis, status, reports, or the Workbench trust boundary.

## Approved scope

- Add **All**, **Errors**, **Warnings**, **Notes**, and **Valid** controls with current counts.
- Filter syntax, Kubernetes document-structure, deterministic operational, and schema sections while preserving their established order.
- Hide result sections that contain no visible entries.
- Show a precise empty state and visible-versus-total summary for an active filter.
- Keep the Validation tab badge and overall analysis status based on the complete unfiltered analysis.
- Keep the OWASP review profile outside severity filtering because its labels describe coverage boundaries rather than result severity.
- Preserve the active filter while YAML edits recompute the analysis and counts.
- Reset to **All** when the inspection mode changes or input is loaded, cleared, or replaced through a file action.
- Preserve finding navigation, editor selection and scrolling, fix guidance, and Copy YAML actions.
- Provide keyboard-operable buttons, visible focus, pressed-state semantics, and live selection feedback.

## Trust boundary

Filtering is ephemeral presentation state held only in browser memory. It does not alter the analysis object, source YAML, Markdown report, schema evaluation, OWASP profile, or unsaved-state tracking.

The milestone adds no storage, cookies, telemetry, backend, network request, Kubernetes API access, RBAC, ServiceAccount token, cluster credential, or automatic remediation. Existing clipboard and local-download actions remain the only explicit Workbench export boundaries.

## Exclusions

- text search or keyword filtering
- filtering by document, resource, namespace, check family, or OWASP category
- persisted preferences or browser storage
- tree search, drag-and-drop, or display themes
- additional report formats
- new deterministic checks, schemas, or OWASP mappings
- large-file processing guarantees
- backend processing, cluster access, deployment controls, or remediation

## Acceptance criteria

- **All** matches the existing Validation result order.
- Every control shows an accurate current count and exposes its selected state.
- An active filter displays only entries at that level and hides empty result sections.
- A filtered-empty state distinguishes the selected subset from the complete analysis.
- OWASP coverage remains visible and semantically separate.
- Tab badge, overall status, and Markdown reports continue to represent the complete analysis.
- YAML edits preserve the selected filter and recompute counts.
- Mode changes, sample loading, file opening, and clearing reset the filter to **All**.
- Finding links, line selection, automatic editor scrolling, fix guidance, and Copy YAML continue to work.
- Focus remains visible and on the selected control after activation; selection changes are announced.
- Automated tests cover every level, counts, empty results, recomputation, resets, OWASP separation, focus and pressed state, and report isolation.
- Validator reproducibility, the complete automated suite, production build, CSP scan, dependency audit, repository manifest validation, whitespace checks, and a non-publishing multi-architecture build pass before release consideration.
- Live browser acceptance uses a multi-document manifest containing multiple result levels.

## Implementation state

- Added browser-memory filter state independent of `analyzeYaml()` and `buildMarkdownReport()`.
- Added counted filter controls and filtered-result summaries to the Validation view.
- Reused the existing result-level values: `error`, `warning`, `note`, and `valid`.
- Kept OWASP review-profile rendering outside the filtered result sections.
- Added reset behavior at mode, sample/file-load, and clear boundaries while preserving the selected filter during edits.
- Added DOM interaction coverage for level filtering, counts, empty states, OWASP separation, recomputation, reset behavior, focus, pressed state, and complete-report isolation.
- Advanced application and lockfile candidate metadata to `0.8.0`.
- Staged and deployed the approved Kubernetes Deployment-only update with `0.8.0` labels and the immutable OCI index digest.

## Gated delivery workflow

1. Planning approval — complete.
2. Implementation approval — complete.
3. Local automated verification, Windows validation, and browser source acceptance — complete.
4. Branch and image publication — complete after separate approval.
5. Deployment-manifest mutation — complete after separate approval.
6. Cluster deployment — complete after separate approval.
7. Live browser acceptance — complete after separate approval.
8. Pull-request readiness — complete after separate approval.
9. Merge — complete through PR #20 at `6fa5092`.

## Validation evidence

- All 74 automated tests pass across analyzer, schema, OWASP profile, formatting diff, Markdown report, and DOM interaction suites.
- The DOM suite covers every filter level, accurate counts, filtered-empty messaging, edit-time recomputation, mode/sample/file/clear resets, OWASP separation, focus and pressed state, filtered finding navigation, Copy YAML, and complete-report isolation.
- Validator reproducibility passes for all 12 bundled Kubernetes resources.
- The production build completes successfully; the existing bundle-size advisory remains non-blocking.
- Strict-CSP validation confirms the production JavaScript contains no eval or Function-constructor usage.
- Dependency audit reports zero vulnerabilities.
- Repository Kubernetes manifest validation and whitespace validation pass.
- The tracked Workbench Deployment and validator expectation are pinned to immutable `0.8.0` at OCI index `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`.
- This workspace has no Docker client; the established GitHub pull-request workflow completed the non-publishing AMD64/ARM64 build successfully.
- The remote browser surface could not reach the workspace loopback server; operator source and live-cluster browser reviews subsequently completed on Windows.
- Draft PR #20 opened from remote source commit `82b291e`; Workbench CI run 137 passed.
- Non-publishing AMD64/ARM64 Docker build run 139 passed without publishing an image.
- Windows validation passed from a clean lockfile installation with all 74 tests green.
- Operator browser review accepted the counted filters, level isolation, empty-section behavior, OWASP separation, stable complete-analysis indicators, finding navigation, complete Markdown report behavior, edit-time recomputation, and reset boundaries.
- Source acceptance completed before the separately approved image-publication step.
- After explicit approval, tag `forge-yaml-workbench-v0.8.0` targeted accepted source commit `1d8a487ada5e053ca806e59195f0807d11564351`.
- Publication workflow run 141 (`34972448064`) completed successfully and published both target architectures.
- The immutable OCI index is `sha256:faa604c336e2de459dee2b079ca0609c13e13f1d8ee030c5369e9c6657db64a3`.
- Independent registry inspection confirmed Linux AMD64 manifest `sha256:dfbfc92e3d4a074d0a421cc3fdb7937f4288937af291aac71ec9a0dc3786d536` and Linux ARM64 manifest `sha256:2db1d88fe7357452f82256e81a4d56ef52d3ddc72bffe0f31524adab524ce615`; the remaining two OCI-index entries are BuildKit attestations.
- The reviewed Deployment-only diff contained only the two `0.8.0` version labels, immutable image update, last-applied annotation, and expected generation preview; repository validation and server-side dry-run passed.
- The approved rollout completed successfully with one Ready Pod on `forge-node-03`, zero restarts, and a runtime ImageID matching the pinned OCI index digest.
- The EndpointSlice settled to the new Pod only. Fresh `/healthz` and application requests through NodePort `30081` returned HTTP 200 with the expected Content Security Policy and `X-Content-Type-Options: nosniff`.
- Live browser acceptance passed all nine checks for counted filters, level isolation, hidden empty sections, complete-analysis indicators, edit-time recomputation, reset boundaries, complete Markdown reports, finding navigation, scrolling, guidance, and Copy YAML.
- PR readiness completed after all three head workflows passed. PR #20 merged into `main` at `6fa5092210633abde28335b76dcad1e085578789` on 2026-09-15.
