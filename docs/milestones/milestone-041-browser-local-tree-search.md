# Milestone 041 — Browser-local YAML tree search

**Status:** Immutable `0.9.0` deployed and live browser-accepted; pull-request readiness pending separate approval
**Started:** 2026-09-15
**Branch:** `codex/milestone-041-tree-search`
**Baseline:** `main` at `e1f48d94a3c88e3a459dedc5af3d9d6537940381`
**Candidate release:** `0.9.0`

## Goal

Make larger YAML trees easier to inspect by adding literal, browser-local search with deterministic navigation while preserving the Workbench trust boundary and existing analysis behavior.

## Approved scope

- Search mapping keys, scalar values, and canonical YAML paths with case-insensitive literal substring matching.
- Represent ordinary mapping keys with dot notation, sequence positions with bracket indexes, and other mapping keys with quoted bracket notation.
- Count each matching tree node once, even when more than one of its searchable fields matches.
- Order matches by document order and depth-first tree order.
- Show total and active-position counts with Previous, Next, and Clear controls.
- Wrap next and previous navigation at either end of the result set.
- Expand every ancestor required to reveal a matching node.
- Highlight every matching row, distinguish the active row, and mark matching text in displayed keys, scalar values, and paths.
- Keep focus in the search controls while navigation scrolls the active result into view.
- Support Enter, Shift+Enter, Escape, and Tree-tab Ctrl+F or Cmd+F behavior.
- Announce match totals, active positions and paths, no-match states, and cleared states through a polite live region.
- Preserve and recompute a query through ordinary edits, temporary parser failures, formatting, and tab changes.
- Reset search for inspection-mode changes, sample loading, file loading, and confirmed editor clearing; preserve it when clearing is cancelled.

## Trust boundary

The search index is derived only from each parsed document's in-memory `raw` value. Query, match, and navigation state exist only in browser memory and do not change YAML analysis, Validation filters, Markdown reports, or unsaved-state tracking.

The milestone adds no storage, cookie, telemetry, backend processing, network request, Kubernetes API access, RBAC, ServiceAccount token, credential, deployment control, or cluster mutation.

## Exclusions

- replacement
- regular expressions
- Validation-result search
- persisted history or preferences
- backend or network processing
- Kubernetes API access or credentials
- cluster mutation or automatic remediation
- drag-and-drop, display themes, additional export formats, or large-file guarantees

## Acceptance criteria

- Keys, scalar strings, numbers, booleans, `null`, and canonical paths are searchable in both inspection modes.
- Matching is literal and case-insensitive, and each node contributes at most one match.
- Multi-document and depth-first ordering is stable.
- Counts, active position, navigation wrapping, ancestor expansion, visual marking, active state, and scrolling are correct.
- Native tree disclosure behavior and visible focus remain intact.
- Search controls have explicit labels, native keyboard operation, shortcuts, polite status announcements, and semantic active-result state.
- Edits and formatting preserve and recompute search; temporary invalid YAML retains the query for recovery.
- Mode changes, sample loading, file loading, and confirmed clearing reset search; a cancelled clear does not.
- Validation filters, complete Markdown reports, downloads, and report previews remain independent of Tree search.
- The complete automated suite, validator reproducibility, production build, CSP scan, dependency audit, repository manifest validation, whitespace checks, Windows validation, and non-publishing AMD64/ARM64 build pass before release consideration.

## Implementation state

- Added a deterministic helper for canonical paths, depth-first indexing, literal matching, and safe highlight ranges.
- Added the Tree search region, counted status, navigation controls, ancestor expansion, match presentation, active state, and keyboard behavior.
- Added helper and Happy DOM tests for matching, ordering, navigation, expansion, focus, announcements, editing, formatting, parser recovery, and reset boundaries.
- Advanced application and lockfile candidate metadata to `0.9.0`.
- Updated only the tracked Deployment version labels and immutable image reference for the separately approved `0.9.0` rollout.

## Gated delivery workflow

1. Planning approval — complete.
2. Local implementation approval — complete.
3. Local automated verification, Windows validation, and browser source review — complete.
4. Source and image publication — complete after separate approval.
5. Deployment-manifest mutation — complete after separate approval.
6. Cluster deployment — complete after separate approval.
7. Live browser acceptance — complete after separate approval.
8. Pull-request readiness — pending separate approval.
9. Merge — pending separate approval.
10. Post-merge cleanup — pending separate approval.

## Validation evidence

- All 83 automated tests pass across analyzer, schema, OWASP profile, formatting diff, Markdown report, Tree search helper, and DOM interaction suites.
- Validator reproducibility passes for all 12 bundled Kubernetes resources.
- The production build completes successfully; the established bundle-size advisory remains non-blocking.
- Strict-CSP validation confirms the production JavaScript contains no eval or Function-constructor usage.
- Dependency audit reports zero vulnerabilities.
- Repository Kubernetes validation, 23 supporting Python tests, and whitespace validation pass.
- The tracked Workbench Deployment and repository validator pin immutable `0.9.0` at OCI index `sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581`.
- The established GitHub workflow completed the non-publishing AMD64/ARM64 build successfully.
- The cloud browser cannot reach the workspace loopback server (`ERR_BLOCKED_BY_CLIENT`), so visual browser review remains an explicit operator source-acceptance item.
- Draft PR #22 opened from connector-authored commit `20800196d202f6a6b58c37dc73bb49ffe529a2d6`; its tree SHA exactly matches the locally accepted source tree.
- Workbench CI run 143 passed.
- Non-publishing AMD64/ARM64 Docker build run 145 passed without publishing an image.
- Windows validation passed from a clean lockfile installation with all 83 tests, validator reproducibility, production build, CSP scan, and zero-vulnerability audit green.
- Operator browser review passed key, scalar-value, and path matching; counts; wrapping navigation; ancestor expansion; visible and active highlights; keyboard and focus behavior; live status; edit and parser recovery; formatting and report isolation; reset boundaries; and default-expansion restoration.
- Source acceptance completed before the separately approved tag and image publication; immutable `0.8.0` remained the tracked and live deployment throughout that gate.
- After explicit approval, tag `forge-yaml-workbench-v0.9.0` targeted accepted source commit `b2a946f9e39ab3f7e1a6bc35ad8bd62297902ca9`.
- Publication workflow run 147 (`35003003075`) completed successfully and published both target architectures.
- The immutable OCI index is `sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581`.
- Independent registry inspection confirmed Linux AMD64 manifest `sha256:4cd48baf0f913b944efa4206302d828107674f7ea7e20543972479d09866dc86` and Linux ARM64 manifest `sha256:e26f85a206a2b564928e285f34253b72b5c8890f99d2eb0af702bfcfdecc9d7b`.
- Repository validation and the approved Deployment-only live diff passed before rollout; the diff changed only generation, two version labels, and the immutable image reference.
- Deployment generation 13 completed with one available and Ready Pod on `forge-node-03`, zero restarts, and runtime ImageID `docker.io/wmstipes/signalforge-yaml-workbench@sha256:9e46b6477cdfebd7a930da6fa608e35a0a428171431a7c73bea043f77aea8581`.
- EndpointSlice `forge-yaml-workbench-bjzkq` reported ready endpoint `10.244.54.202:8080`; private-lab NodePort `30081` returned HTTP 200 for `/healthz` and `/` with the expected CSP and security headers.
- Operator live browser acceptance passed key, scalar-value, and canonical-path matching; one-node counts; wrapping navigation; ancestor expansion; visible and active highlighting; keyboard, focus, and live-status behavior; edit and parser recovery; formatting and report isolation; reset boundaries; cancelled-clear preservation; and default-expansion restoration.
