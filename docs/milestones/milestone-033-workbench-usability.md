# Milestone 033 — Forge YAML Workbench usability

Started: 2026-09-12

Status: Implementation, browser acceptance, and versioned `0.1.2` publication complete in draft PR #9. Deployment, final documentation reconciliation, and merge remain pending separate checkpoints.

## Goal

Make common Workbench actions unambiguous and make parser failures easier to locate without changing the browser-local processing boundary or adding Kubernetes credentials.

## Bounded scope

- Report whether Format changed the YAML, found it already normalized, or failed.
- Attach line and column data to parser diagnostics.
- Let a user select the reported editor line from a diagnostic.
- Preserve an opened YAML filename during download.
- Add keyboard shortcuts for Open, Format, and Download.
- Confirm before Clear discards edits made since the last load or download.
- Improve tab accessibility state.
- Add DOM interaction tests for the critical browser flows.
- Correct the post-merge state in the Milestone 032 record.

## Preserved boundaries

- YAML remains in browser memory and is not sent to a backend.
- The application receives no Kubernetes credentials or API access.
- No server-side persistence is introduced.
- Findings remain bounded guidance rather than API-server admission guarantees.
- Image publication and cluster deployment require later, separate approval.

## Browser acceptance evidence

- Formatting the existing sample reported that it was already normalized without changing its two-document structure.
- Formatting compact flow-style YAML through `Ctrl+Shift+F` visibly produced five-line block-style YAML and retained one valid Pod document.
- A duplicate `kind` key opened Validation, reported line 3 column 1, and the location control selected exactly that editor line.
- Replacing the selected duplicate restored one valid document.
- The first diagnostic-navigation test exposed stale red action feedback after correction; commit `1f90eaf` replaced stale results with neutral `Editing YAML` feedback, and the repeated browser check passed.
- `Ctrl+O` opened a YAML file, `Ctrl+S` downloaded it with its original filename, and Clear preserved edited YAML when cancellation was selected before clearing it after confirmation.

## Release publication

Mike explicitly approved publication of `0.1.2`. Tag `forge-yaml-workbench-v0.1.2` points to release commit `74fa2d0`, and [GitHub Actions run 34714312591](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34714312591) completed successfully.

Published OCI image index:

```text
wmstipes/signalforge-yaml-workbench:0.1.2
sha256:07f34be33c55bca5b7bf5321e5d149e4831ce520c9efbdd98233468a1a50e3c7
```

Platform manifests:

- AMD64: `sha256:b52ee9a984cfc5041eb4eecb61f1f0a4cdaa0ffbdea2174801e46fbe80e43404`
- ARM64: `sha256:1682d1564dce644c9d19918a97f8898d72eedcc16b0e781d9570b3dccf43f585`

## Deferred follow-on milestones

- Milestone 034: deeper deterministic operational checks with paths, explanations, and suggested corrections.
- Milestone 035: offline schema validation against a pinned Kubernetes version, with unknown CRDs reported as schema unavailable.
- Later Workbench increments: formatting diff, copy/export tools, filtering, tree search, drag-and-drop, display preferences, and bounded large-file processing.

## Acceptance gates

- [x] Locked clean installation passes.
- [x] Analyzer and DOM interaction tests pass locally.
- [x] Production build passes locally.
- [x] Dependency audit reports zero vulnerabilities locally.
- [x] Pull-request CI and multi-architecture non-publishing image build pass.
- [x] Browser acceptance confirms feedback, diagnostic navigation, filename preservation, shortcuts, and clear protection.
- [x] Version `0.1.2` publication was separately approved and verified.
- [ ] Any live Deployment update is separately dry-run, diff-reviewed, approved, and verified.
