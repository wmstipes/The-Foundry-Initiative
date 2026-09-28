# Contributing

The Foundry Initiative currently uses a lightweight, review-first workflow.

## Working approach

1. Create a focused branch from `main` using `codex/<description>` for assisted
   work or `feature/<description>` for other focused changes.
2. Keep each change small enough to review and explain.
3. Add or update documentation alongside code.
4. Run relevant tests and checks before opening a pull request. Use the
   [testing and validation guide](docs/testing-and-validation.md) to identify
   the applicable suites and evidence boundaries.
5. Open pull requests as drafts until the work is ready for final review.

GitHub's pull-request template records validation, documentation impact,
security and release impact, known limitations, and follow-up work. Bug and
feature issue forms are available for non-sensitive reports. Suspected
vulnerabilities must use the private process in [SECURITY.md](SECURITY.md), not
a public issue.

When a change adds, removes, parameterizes, relocates, or changes discovery of
tests, update the testing guide's dated inventory and suite description in the
same pull request. Report named suite counts rather than an unlabeled total.

## Documentation maintenance

Before closing a change that affects operation or access, review the
[documentation map](docs/README.md). Update current status, architecture,
the affected runbook, and a dated evidence record as applicable. Keep observed
results distinct from planned work and static validation. Historical milestone
results retain their original dates and test counts; add a subsequent-outcome
note when a historical procedure could otherwise be mistaken for current guidance.

Wiki changes start in `docs/wiki`. Validate those files, publish the reviewed
copies to the separate Wiki repository within the authorized task scope, and
verify an exact copy with `validate-wiki-front-door.py --wiki-dir <checkout>`.
Record the Wiki commit in the change record. Publish only links that already
resolve on `main`; new target files must reach `main` before the Wiki links do.
The Wiki remains navigation; current procedures and evidence live in this repository.

## Commit messages

Use short, intentional commit messages that describe the result, for example:

- `Add initial project roadmap`
- `Create first experiment scaffold`
- `Document architecture decision process`

## Pull requests

Each pull request should explain:

- what changed
- why it changed
- how it was validated
- any known limitations or follow-up work

## Git patch reference

See [Understanding Git patch files](docs/reference/git-patch-files.md) for the patch format, safe application workflow, common failures, and recovery guidance used by this repository.

## Project values

- Progress over perfection
- Evidence over self-judgment
- Clarity over unnecessary complexity
- Sustainable effort over burnout
- Learning through finished work
