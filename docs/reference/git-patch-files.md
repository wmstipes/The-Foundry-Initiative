# Understanding Git patch files

A `.patch` file is a plain-text description of changes between two versions of files. It is usually written in Git's **unified diff** format. It is not a programming language, does not create a commit by itself, and does not automatically execute the code it contains.

SignalForge uses patches when a reviewed change must move between separate Git workspaces. The patch preserves exact additions, removals, file paths, and enough surrounding context for Git to verify that it is being applied to the intended baseline.

## Basic anatomy

```diff
diff --git a/docs/example.md b/docs/example.md
index 1111111..2222222 100644
--- a/docs/example.md
+++ b/docs/example.md
@@ -3,4 +3,5 @@ Existing section
 unchanged context
-old line
+new line
+another new line
```

| Marker | Meaning |
| --- | --- |
| `diff --git a/... b/...` | Identifies the old and new path for the affected file. |
| `index ...` | Shows abbreviated Git object IDs and, commonly, the file mode. |
| `--- a/...` | Identifies the old file. |
| `+++ b/...` | Identifies the new file. |
| `@@ -3,4 +3,5 @@` | Begins a change block, called a hunk, and describes its old and new line ranges. |
| A leading space | Context that should already exist and remains unchanged. |
| A leading `-` | A line removed from the old version. |
| A leading `+` | A line added to the new version. |

The `a/` and `b/` prefixes normally represent the two sides of the comparison. They are not literal directories in the repository when the patch is applied normally.

## Reading a hunk header

This header:

```diff
@@ -10,6 +10,9 @@
```

means:

- the old block begins around line 10 and contains 6 lines;
- the new block begins around line 10 and contains 9 lines.

Line numbers are navigation hints. Git primarily uses the unchanged context around a hunk to locate it safely, which is why a patch can still apply after unrelated lines move elsewhere in the file.

## File operations

Patches can represent more than edited lines.

### New file

```diff
new file mode 100644
--- /dev/null
+++ b/docs/new-file.md
```

`/dev/null` on the old side means the file did not previously exist.

### Deleted file

```diff
deleted file mode 100644
--- a/docs/old-file.md
+++ /dev/null
```

`/dev/null` on the new side means the patch deletes the file. Treat this as a destructive change and review it carefully.

### Renamed file

```diff
similarity index 100%
rename from docs/old-name.md
rename to docs/new-name.md
```

Git may record a rename together with additional content changes.

### File mode or binary changes

A patch may change executable permissions or include encoded binary changes. `git diff --binary` is needed when binary content must be represented. Binary patches are harder to inspect manually, so verify their source and resulting file hashes when that matters.

## Safe SignalForge workflow

Run these commands from the repository root on the intended branch:

```powershell
git status --short --branch
git apply --check "$env:USERPROFILE\Downloads\change.patch"
git apply "$env:USERPROFILE\Downloads\change.patch"
git diff --check
git diff --stat
git status --short
```

What each step establishes:

1. `git status --short --branch` confirms the branch and exposes existing work that must not be overwritten.
2. `git apply --check` performs a dry validation. No output with exit code zero means the patch should apply cleanly.
3. `git apply` changes the working tree but does not stage, commit, or push anything.
4. `git diff --check` detects whitespace errors in the resulting unstaged changes.
5. `git diff --stat` summarizes affected files and line counts.
6. `git status --short` shows the exact modified, added, and deleted paths.

After reviewing and testing the result:

```powershell
git add <reviewed-paths>
git diff --cached --check
git diff --cached --stat
git commit -m "Describe the completed result"
git push
```

Staging explicit paths is preferable when unrelated work is present. `git add .` is reasonable only after confirming that every working-tree change belongs to the same commit.

## Inspecting a patch before applying it

Because a patch is text, it can be opened in VS Code, Vim, Notepad, or another text viewer. Git can also summarize it:

```powershell
git apply --stat "$env:USERPROFILE\Downloads\change.patch"
git apply --summary "$env:USERPROFILE\Downloads\change.patch"
```

Review especially:

- every affected path;
- deleted files and removed safeguards;
- changes under `.github/workflows`, `scripts`, Kubernetes manifests, or dependency files;
- commands that write externally, change credentials, delete resources, or weaken validation;
- unexpected binary files or file-mode changes.

A patch does not execute while being viewed or applied, but scripts and workflows introduced by it may execute later when someone runs them or CI processes them.

## Common failures

### `patch does not apply`

The current files do not match the context expected by the patch. Common causes include:

- the branch is based on a different commit;
- the patch was already applied;
- a file was edited after the patch was prepared;
- line-ending or whitespace conversion changed the context.

Do not force the patch immediately. Confirm the branch, baseline commit, working-tree state, and patch source first.

### `already exists in working directory`

The patch is trying to create a file that is already present. Determine whether the patch was applied previously or whether an unrelated file has the same path.

### Whitespace warnings

Run `git diff --check` after application. Windows CRLF and repository LF line endings can produce confusing messages when Git configuration differs between workstations. Inspect `.gitattributes` and `core.autocrlf` before performing a broad line-ending rewrite.

### Partial or rejected application

Avoid `git apply --reject` during the normal SignalForge workflow. It can apply some hunks while leaving `.rej` files for the rest, producing a state that is easier to misunderstand. Prefer returning to the known pre-application state and preparing a patch for the correct baseline.

## Undoing an uncommitted patch

If the patch is the only working-tree change and has not been edited further, it can often be reversed with:

```powershell
git apply --reverse "$env:USERPROFILE\Downloads\change.patch"
```

Always run the reverse check first:

```powershell
git apply --reverse --check "$env:USERPROFILE\Downloads\change.patch"
```

Do not use broad destructive commands such as `git reset --hard` merely to undo a patch; they can erase unrelated work. If the tree contains mixed changes, identify and recover the affected paths deliberately.

## Patch files versus commit patches

Two related formats are common:

| Workflow | Creation | Application | Result |
| --- | --- | --- | --- |
| Working-tree patch | `git diff --binary --output=change.patch` | `git apply change.patch` | Changes working files only. |
| Commit/email patch | `git format-patch -1 <commit>` | `git am <patch>` | Recreates the commit and its author/message metadata. |

SignalForge handoffs normally use working-tree patches so the operator can inspect, test, stage, and commit the result locally. Do not substitute `git am` unless the artifact was intentionally created with `git format-patch` and preserving its commit metadata is desired.

## Useful mental model

Think of a patch as a reviewable set of instructions:

> In this file, find this surrounding context, remove these lines, and add these lines.

The context makes the instructions baseline-sensitive. The `--check` step confirms that Git can follow all of them before it changes the working tree.

