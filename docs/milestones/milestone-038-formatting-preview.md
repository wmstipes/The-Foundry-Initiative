# Milestone 038 — Formatting preview

**Status:** Implementation in progress  
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

## Trust boundary

Parsing, formatting, comparison, and preview rendering remain in browser memory. The Workbench does not send YAML to a backend, contact Kubernetes, obtain credentials, or apply resources.
