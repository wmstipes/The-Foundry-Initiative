# The Foundry Initiative

The Foundry Initiative is a personal engineering and learning project focused on rebuilding confidence through deliberate practice, useful systems, and visible progress.

This repository is a practical workspace for:

- applied AI and machine learning experiments
- DevOps, platform engineering, and infrastructure projects
- architecture notes and technical decision records
- structured learning plans and reflections
- small, finishable projects that demonstrate growth over time

## Guiding principle

Progress does not need to be dramatic to be real. The goal is to keep building, documenting, learning, and turning experience into evidence.

## Repository map

- `docs/` — project vision, architecture, decisions, and learning notes
- `src/` — implementation code
- `tests/` — automated tests
- `experiments/` — prototypes and exploratory work
- `ROADMAP.md` — phased goals and milestones
- `CONTRIBUTING.md` — working conventions for the project

## Current status

First working artifact phase: building and validating `foundry-check` as the repository's initial implementation.

## First implementation: foundry-check

`foundry-check` is a small Python command-line tool that evaluates whether a local repository has a reasonable project foundation. It uses only the Python standard library at runtime and never reads secret contents.

### Requirements and installation

Python 3.11 or newer and Git are required. From the repository root, install the project locally:

```bash
python -m pip install -e .
```

### Usage

The repository argument is optional and defaults to the current directory. Text is the default output format.

```bash
foundry-check
foundry-check /path/to/repository
foundry-check . --format text
foundry-check . --format json
```

### Checks

The command performs exactly five checks:

1. `README.md` and `.gitignore` exist as files at the repository root.
2. `src` and `tests` exist as directories at the repository root.
3. `src` and `tests` contain substantive files rather than only placeholders or generated Python files.
4. `docs/vision.md`, `docs/architecture.md`, and `docs/learning-journal.md` exist.
5. Git-tracked filenames do not look like common secret or private-key files. Only filenames are inspected; contents are never opened or displayed.

If Git is unavailable or the target is not a Git repository, the fifth check returns a warning instead of failing or crashing.

### Exit codes

- `0` — no checks failed; warnings may be present
- `1` — one or more readiness checks failed
- `2` — invalid arguments, an inaccessible target path, or an unexpected execution error

### Passing example

```text
Foundry Check: /work/example

PASS  Required baseline files
      README.md and .gitignore are present.
PASS  Expected directories
      src and tests directories are present.
PASS  Implementation and test content
      src and tests contain substantive files.
PASS  Baseline documentation
      Vision, architecture, and learning journal documents are present.
PASS  Suspicious tracked secret filenames
      No suspicious tracked secret filenames were found.

Summary: 5 passed, 0 warning, 0 failed
```

### Failing example

```text
Foundry Check: /work/incomplete-example

FAIL  Required baseline files
      Required baseline files are missing.
      - README.md
PASS  Expected directories
      src and tests directories are present.
FAIL  Implementation and test content
      Implementation or test directories lack substantive files.
      - tests
FAIL  Baseline documentation
      Baseline documentation is incomplete.
      - docs/architecture.md
PASS  Suspicious tracked secret filenames
      No suspicious tracked secret filenames were found.

Summary: 2 passed, 0 warning, 3 failed
```

### JSON example

```json
{
  "repository": "/work/example",
  "status": "pass",
  "summary": {
    "passed": 5,
    "warnings": 0,
    "failed": 0
  },
  "checks": [
    {
      "id": "baseline_files",
      "name": "Required baseline files",
      "status": "pass",
      "message": "README.md and .gitignore are present.",
      "details": []
    }
  ]
}
```
