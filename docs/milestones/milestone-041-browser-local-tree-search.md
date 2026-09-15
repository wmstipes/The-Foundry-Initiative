# Milestone 041 — Browser-local YAML tree search

**Status:** Implementation complete; source acceptance pending
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
- Left the tracked Kubernetes Deployment and live immutable `0.8.0` runtime unchanged.

## Gated delivery workflow

1. Planning approval — complete.
2. Local implementation approval — complete.
3. Local automated verification — complete; visual and Windows source review pending.
4. Source publication and image publication — pending separate approval.
5. Deployment-manifest mutation — pending separate approval.
6. Cluster deployment — pending separate approval.
7. Live browser acceptance — pending separate approval.
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
- The tracked Workbench Deployment and repository validator remain unchanged at immutable `0.8.0`.
- This workspace has no Docker client, so the non-publishing AMD64/ARM64 build remains for the established GitHub workflow after publication approval.
- The cloud browser cannot reach the workspace loopback server (`ERR_BLOCKED_BY_CLIENT`), so visual browser review remains an explicit operator source-acceptance item.
