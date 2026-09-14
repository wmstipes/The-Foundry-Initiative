# Milestone 039 — Browser-local Markdown analysis reports

**Status:** Immutable 0.7.0 image published; deployment review pending
**Started:** 2026-09-14
**Branch:** `codex/milestone-039-markdown-report`
**Baseline:** `main` at `3b562ef0c4be7fc15fd5bd3cbe98e7d5ca73373c`

## Goal

Generate a deterministic Markdown representation of the current Workbench analysis in browser memory, let the operator review it, and require an explicit action before copying it to the operating-system clipboard or downloading it as a local file.

## Approved scope

- Add a pure report generator that accepts the current filename and `analyzeYaml()` result.
- Support Kubernetes and General YAML inspection modes.
- Open a browser-local Markdown preview through an explicit **Generate report** action.
- Keep the editor and its unsaved-state tracking unchanged while generating, reviewing, copying, downloading, or cancelling a report.
- Provide explicit **Copy Markdown** and **Download .md** actions.
- Close the preview without an external side effect through **Cancel** or Escape.
- Invalidate a prepared report if the YAML source, inspection mode, or opened file changes.
- Derive a predictable report filename from the YAML filename, such as `deployment-report.md`.
- Preserve accessible dialog semantics, initial focus, focus containment, and focus restoration.
- Keep report generation deterministic and directly unit-testable without browser APIs.

## Report contract

The Markdown report will contain only analysis-derived information:

- report title, source filename, and inspection mode
- parsed-document and finding counts
- per-document summaries
- YAML syntax diagnostics
- Kubernetes document-structure errors
- deterministic operational findings
- YAML paths and line or column locations when available
- recommended changes, bounded example YAML, cautions, and security references
- Kubernetes schema status pinned to the Workbench's bundled schema version
- OWASP Kubernetes Top 10 review-profile coverage and boundary language
- explicit limitations and next-step guidance

The report will not reproduce the complete source YAML. User-controlled text will be escaped or fenced safely so that names, paths, messages, and examples cannot unintentionally alter the report structure.

## User workflow

1. The operator edits or opens YAML and reviews the live analysis.
2. **Generate report** creates a snapshot in browser memory and opens a Markdown preview.
3. **Copy Markdown** copies the reviewed snapshot to the operating-system clipboard.
4. **Download .md** downloads the reviewed snapshot without marking the YAML source as saved.
5. **Cancel** or Escape discards the snapshot without copying or downloading anything.

## Trust boundary

Parsing, schema lookup, operational evaluation, OWASP mapping, Markdown generation, and report preview remain in browser memory. The Workbench does not send YAML or reports to a backend, contact Kubernetes, obtain credentials, persist report history, or apply resources.

Copy and Download are deliberate trust-boundary crossings:

- **Copy Markdown** places manifest-derived report content on the operating-system clipboard.
- **Download .md** writes manifest-derived report content to a local file selected through normal browser download behavior.

The preview will state that exported reports can contain resource names, namespaces, paths, findings, and recommendations derived from the supplied YAML.

## Exclusions

This milestone does not add:

- PDF, HTML, JSON, or SARIF export
- full source-YAML embedding
- Markdown-to-HTML rendering
- report history, browser storage, or server-side persistence
- upload, sharing, or remote report delivery
- finding filters or tree search
- drag-and-drop or display preferences
- cluster access, deployment controls, or automated remediation
- broader large-file guarantees

## Acceptance criteria

- Kubernetes and General YAML produce deterministic Markdown reports from their current analysis results.
- Empty and invalid inputs produce bounded, explicit report states without inventing analysis.
- Multi-document summaries preserve document order.
- Kubernetes reports distinguish syntax, document structure, operational findings, schema results, and OWASP coverage.
- General YAML reports omit Kubernetes-specific schema, operational, and OWASP sections.
- The complete source YAML is absent from the report.
- Markdown-sensitive values and code-fence content cannot corrupt the report structure.
- Generating a report does not copy, download, alter, or mark the YAML as saved.
- Copy and Download use exactly the reviewed report snapshot.
- Report download uses a predictable `*-report.md` filename and does not change the YAML download filename.
- Cancel and Escape close the preview without an external side effect.
- Focus begins inside the preview, remains contained, and returns to the Generate report control.
- Editing, changing inspection mode, opening another file, loading the sample, or clearing invalidates any prepared report.
- Existing analyzer, schema, OWASP, formatter, diff, and YAML-download behavior remains covered.
- Validator reproducibility, automated tests, production build, strict-CSP compatibility, dependency audit, repository validation, whitespace checks, and local browser acceptance pass before release consideration.

## Implementation state

- Added `src/report.js` as a pure deterministic report generator with no DOM or network dependency.
- Added report unit coverage for Kubernetes, General YAML, empty input, invalid syntax, multi-document ordering, schema boundary states, Markdown escaping, safe code fences, and portable filenames.
- Added an accessible browser-local preview with explicit Copy Markdown, Download .md, Cancel, and Escape actions.
- Added focus containment and restoration following the established formatting-preview interaction.
- Added DOM coverage for no-export preview generation, exact-snapshot copying, report filename selection, unsaved-state preservation, cancellation, keyboard behavior, mode isolation, and stale-report invalidation.
- Updated the candidate application and lockfile version to `0.7.0`.
- Left the Kubernetes Deployment and accepted `0.6.0` runtime unchanged.

Automated validation, local browser acceptance, and the separately approved image publication are complete. Manifest mutation, cluster deployment, live acceptance, and pull-request merge remain separately gated; the running `0.6.0` deployment is unchanged.

## Validation evidence

- All 69 tests passed across analyzer, schema, OWASP profile, formatting diff, Markdown report, and DOM interaction suites.
- Validator reproducibility passed for all 12 bundled Kubernetes resources.
- The production build completed successfully.
- Strict-CSP validation confirmed that the production JavaScript contains no eval or Function-constructor usage.
- Dependency audit reported zero vulnerabilities.
- Repository Kubernetes manifest validation passed.
- Repository whitespace validation passed with a clean worktree.
- Initial browser review confirmed report generation, Copy, and Download behavior and identified missing visible in-modal action feedback.
- Browser acceptance confirmed Kubernetes and General YAML report generation, unchanged editor content, correct report sections and mode isolation, clipboard copy, predictable Markdown download naming, Escape cancellation, and preservation of unsaved YAML state.
- Browser review identified that successful Copy and Download actions initially reported status only behind the modal.
- The corrected candidate provides an in-modal live status plus a highlighted **Copied** or **Downloaded** button state; final browser confirmation passed for both actions.
- Draft PR #18 opened against `main` without authorizing publication, deployment, readiness, or merge.
- Workbench CI run 108 passed all pull-request checks.
- Docker build run 110 successfully built the AMD64 and ARM64 candidate through the pull-request path with `push: false`; no image was published.
- After explicit publication approval, workflow run `34886290349` built and pushed `wmstipes/signalforge-yaml-workbench:0.7.0` from source commit `84123ae842ce85d8e37bd02d8e96f3fb4d9765ae` for `linux/amd64` and `linux/arm64`.
- The published OCI index digest is `sha256:f9f5939910382911b23e78609ea5690e617e2a446c3dd707da2c1c6852a8a6d2`.
- Independent registry inspection confirmed Linux AMD64 manifest `sha256:1bae69ab2d812f6ee2d8209a01afdc31dc98b28d2c5b4e1925edc7847512448e` and Linux ARM64 manifest `sha256:4aa7295d62481d12973cde2d46ba0a258e1858dc5ac192d89a132134178f269d`.

## Candidate release

Application version `0.7.0` was published only after explicit approval. The immutable OCI index is `sha256:f9f5939910382911b23e78609ea5690e617e2a446c3dd707da2c1c6852a8a6d2`. Publication does not authorize manifest mutation or cluster deployment.

## Gated delivery workflow

1. Approve and commit the planning record.
2. Implement and validate source changes on the milestone branch.
3. Review the complete diff and automated checks.
4. Obtain explicit approval before publishing an immutable multi-architecture image.
5. Record the published digest and prepare a server-side dry-run and live diff.
6. Obtain explicit approval before changing the cluster Deployment.
7. Complete runtime and browser acceptance.
8. Complete documentation, final review, pull request, and merge through their established gates.
