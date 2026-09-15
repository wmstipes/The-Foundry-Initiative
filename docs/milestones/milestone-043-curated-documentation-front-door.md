# Milestone 043 — Curated documentation front door

**Status:** Complete; cleanup remains separately gated

**Started:** 2026-09-15

**Branch:** `codex/milestone-043-documentation-front-door`

**Baseline:** `main` at `15424d76626dac16127b8d7702289032c4a268ce`

## Goal

Provide a concise GitHub Wiki front door that helps external technical readers and future operators find the right repository documentation without creating a second source of project truth.

## Audience and routes

- Recruiters and hiring managers receive direct routes to the overview, current status, and roadmap.
- Platform and DevOps reviewers receive direct routes to architecture, constraints, observability context, and chronological evidence.
- Operators and the future maintainer receive direct routes to current state and runbooks.
- Learners receive direct routes to the vision, roadmap, and milestone progression.

## Information architecture

The first increment contains only:

- `Home.md`, with a stable project orientation, audience-based routes, and an explicit authority notice.
- `_Sidebar.md`, with persistent navigation to Home and the same authoritative repository destinations.

No footer, secondary Wiki pages, images, tables, generated site, custom style, script, search integration, or analytics are included.

## Authoritative-source boundary

- The main repository is authoritative.
- `ROADMAP.md` owns direction and sequencing.
- `docs/project-status.md` owns current live state.
- `docs/architecture.md` owns design and constraints.
- `docs/milestones` owns chronological evidence.
- `docs/runbooks` owns operator procedures.
- `docs/wiki` owns the reviewed source of the derivative Wiki front door.
- Live Wiki files must match the reviewed repository source byte-for-byte.
- The Wiki does not carry release versions, image digests, live resource state, network addresses, commands, recovery steps, or milestone acceptance evidence.

## Maintenance and mutation model

Routine changes begin under `docs/wiki` in a focused repository branch. Offline validation and normal source review precede a separately approved live Wiki mutation. After mutation, a cloned Wiki checkout must match the repository source exactly, the public pages and destinations must render successfully, and the Wiki commit must be recorded before PR readiness.

Direct edits in the GitHub Wiki browser are not the normal maintenance path. If the Wiki is initially empty, creating its first Home page is part of the separately approved mutation gate because GitHub requires an initial page before the Wiki Git repository can be cloned.

## Accessibility and readability

- Each page has exactly one H1 and no skipped heading levels.
- Link labels describe their destinations without bare URLs or ambiguous “click here” wording.
- Short paragraphs and lists support scanning and narrow screens.
- No information depends on color, icons, images, or custom interaction.
- Native links preserve keyboard navigation and browser zoom behavior.
- The authority notice appears before the navigation choices.

## Link and publication validation

`scripts/validate-wiki-front-door.py` uses only the Python standard library. It:

- requires exactly the approved two source files;
- checks heading hierarchy and descriptive HTTPS links;
- maps same-repository `blob/main` and `tree/main` URLs to local paths and proves the targets exist;
- rejects unsupported external, feature-branch, commit-specific, query, fragment, and raw-content destinations;
- rejects selected volatile operational content;
- requires the authority notice and the approved reader routes;
- verifies sidebar destinations also appear on Home;
- verifies the Restaurant image-publication workflow trigger boundary; and
- optionally compares a cloned Wiki checkout byte-for-byte with `docs/wiki`.

## Restaurant API workflow guardrail

The documentation-only merge at `15424d7` triggered Restaurant API Docker Build run 61 because `.github/workflows/restaurant-api-docker.yml` accepted every push to `main`. That run tested the unchanged application and published floating `latest` plus commit-SHA images.

The bounded correction adds `apps/restaurant-api/**` as the branch-push path. The intended event matrix is:

| Event | Expected result |
|---|---|
| Documentation-only push to `main` | Skip |
| Wiki-source-only push to `main` | Skip |
| Restaurant API source push to `main` | Run |
| `v*.*.*` tag push | Run |
| Manual dispatch | Run |

GitHub does not evaluate path filters for tag pushes, so version-tag publication is preserved. Broader workflow redesign, image provenance, attestations, architecture expansion, and tag-policy changes remain outside this milestone.

## Exclusions

- GitHub Pages, custom domains, and search-engine optimization.
- A copied milestone catalog or duplicated operational documentation.
- Public Wiki editing.
- Historical milestone normalization or broad runbook restructuring.
- Application, image, Kubernetes manifest, cluster, or deployment changes.
- General CI/CD redesign beyond the exact Restaurant API branch-path guardrail.

## Wiki publication evidence

- The live Wiki default branch is `master`.
- The published Wiki commit is `0a945b4cac2ba1c781a55f9aa1a8c389426892e3`.
- Live `Home.md` uses reviewed source blob `2f6857f28bcb0087685707d8b25d0c01fbbf854d`.
- Live `_Sidebar.md` uses reviewed source blob `7cfc6985280fb041fb4ed2593f1863d736249b51`.
- The post-push local and `origin/master` refs matched exactly and the Wiki worktree was clean.
- The initial browser-created Home and sidebar scaffolding commits remain in history; the published commit replaces only their provisional content.
- All repository destinations referenced by the Wiki were confirmed through the connected GitHub API.
- User browser acceptance confirmed correct visible rendering, all navigation destinations, keyboard navigation, readability at 200-percent zoom, and collaborator-only Wiki editing.

## Merge evidence

- PR #25 merged into `main` on 2026-09-15 at 22:10:27 UTC.
- The merge commit is `c42614db59f8b42a3d5e90d0a9e4272f47ed8080`.
- GitHub reported no workflow runs or commit statuses for the merge commit.
- In particular, the Restaurant API Docker publication workflow did not run.
- This is the first live confirmation that a documentation-only merge is skipped by the Milestone 043 path guardrail.

## Deterministic verification

Local acceptance requires:

1. The exact approved baseline and feature branch.
2. A passing Wiki front-door validator.
3. Passing focused unit tests, including all five workflow-event cases.
4. Passing repository tests and existing validators relevant to the changed files.
5. Clean whitespace and a reviewed diff limited to approved scope.

Publication acceptance additionally requires a draft PR with expected files and successful applicable checks. Wiki acceptance requires exact source synchronization, public rendering, link navigation, keyboard and 200-percent-zoom review, restricted editing, and a recorded Wiki commit. The merge must not cause a Restaurant API image publication.

## Gated delivery workflow

1. Planning — complete after explicit approval.
2. Local implementation — complete after explicit approval.
3. Branch publication and draft PR — complete after explicit approval.
4. Live Wiki mutation and browser accessibility review — complete after explicit approval at Wiki commit `0a945b4cac2ba1c781a55f9aa1a8c389426892e3`.
5. Pull-request readiness — complete after explicit approval.
6. Merge — complete at `c42614db59f8b42a3d5e90d0a9e4272f47ed8080`.
7. Cleanup — not authorized.
