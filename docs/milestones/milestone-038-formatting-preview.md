# Milestone 038 — Formatting preview

**Status:** Complete; merged through PR #16 at `4fed28c`  
**Started:** 2026-09-14  
**Branch:** `codex/milestone-038-format-preview`

## Goal

Replace immediate editor mutation with a browser-local, line-oriented preview that lets an operator review deterministic YAML formatting before choosing whether to apply it.

## Scope

- Keep `formatYaml()` as the sole formatting implementation.
- Compare the current and formatted YAML as aligned lines in browser memory.
- Show before and after line numbers with explicit added, removed, and unchanged states.
- Leave the editor unchanged while the preview is open.
- Apply the formatted output only through an explicit **Apply formatting** action.
- Preserve the original input through **Cancel** or Escape.
- Keep the existing empty-input, already-formatted, and parser-error behavior.
- Make `Ctrl+Shift+F` open the same preview workflow.
- Provide dialog semantics, initial focus, focus containment, and focus restoration.
- Bound line alignment work and label the simplified fallback used for unusually large comparisons.

## Exclusions

This milestone does not add:

- character-level diffing
- in-place partial edits
- automatic cluster deployment or cluster access
- copy or report export
- finding filters or tree search
- drag-and-drop
- display preferences
- general large-file processing guarantees

## Acceptance criteria

- Formatting valid changed YAML opens a line-oriented preview without modifying the editor.
- Added and removed lines are visually distinct and include their corresponding line numbers.
- Apply replaces the editor content with exactly the existing formatter output.
- Cancel and Escape close the preview without modifying the editor.
- Keyboard focus begins inside the preview, remains contained, and returns to the Format control on cancellation.
- Already normalized YAML reports that no changes are needed without opening the preview.
- Invalid YAML retains the editor content, selects Validation, and reports the parser failure.
- Kubernetes and General YAML modes use the same formatting preview.
- Multi-document formatting remains parseable and does not create empty documents.
- Automated analyzer, diff, DOM, build, CSP, dependency-audit, repository-manifest, and whitespace checks pass before release consideration.

## Acceptance evidence

- Automated coverage increased to 58 passing tests across analyzer, schema, OWASP profile, line-diff, and DOM interaction suites.
- Final-candidate pull-request Workbench CI run 98 passed validator reproducibility, tests, production build, strict-CSP compatibility, and dependency audit.
- Final-candidate pull-request Docker build run 100 built the AMD64 and ARM64 candidate without publishing it.
- Windows validation passed after making generated-validator comparison neutral to CRLF versus LF checkout differences.
- Repository Kubernetes manifest validation and whitespace checks passed.
- Local browser acceptance confirmed preview display for valid changes, unchanged editor content before approval, Apply, Cancel, and the invalid-YAML route to Validation.
- Invalid test input initially clarified the boundary: formatting normalizes valid YAML but does not guess repairs for syntax errors.
- The reviewed server-side dry-run passed, and the live diff was limited to version labels plus the immutable `0.6.0` image reference before explicit deployment approval.
- The rollout produced one Ready Pod with zero restarts; configured image and runtime ImageID exactly matched OCI index `sha256:4166df67190eaaade054be09c91f0ef8a76e832f290f7383fc4e58c7dd7469bc`.
- The Service retained NodePort `30081`, and its EndpointSlice routed to the Ready Pod on port `8080`.
- Fresh NodePort requests returned HTTP 200 for `/healthz` and the application page with the expected CSP and `X-Content-Type-Options: nosniff` headers.
- Live browser acceptance passed for preview display, unchanged editor content before Apply, Cancel preservation, Apply formatting, invalid-YAML validation behavior, and both Kubernetes and General YAML modes.

## Release state

- Candidate version: `0.6.0`
- Publication workflow: run `34858580511` / run number 101 passed
- Published image: `wmstipes/signalforge-yaml-workbench:0.6.0`
- OCI index: `sha256:4166df67190eaaade054be09c91f0ef8a76e832f290f7383fc4e58c7dd7469bc`
- AMD64 manifest: `sha256:f051ce44976c1abdd2076415edc6476ef57cb8c5e2c7cb196cb1391616ab5f0a`
- ARM64 manifest: `sha256:d5795e44b4553b8bd6b8a96c7ad6e3b574e8b9e7dcdbc80c0ed1f34ef2e01208`
- Tracked Deployment: immutable `0.6.0` image pinned by version and OCI index digest
- Live version: accepted `0.6.0`
- PR state: merged at `4fed28c`
- Post-merge checks: Workbench CI run 107, Kubernetes Manifest Validation run 104, and Restaurant API Docker Build run 53 passed on `main`

## Trust boundary

Parsing, formatting, comparison, and preview rendering remain in browser memory. The Workbench does not send YAML to a backend, contact Kubernetes, obtain credentials, or apply resources.
