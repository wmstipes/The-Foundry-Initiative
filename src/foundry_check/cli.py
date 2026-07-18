"""Command-line parsing and output rendering for foundry-check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence, TextIO

from .checks import run_checks
from .models import CheckResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foundry-check",
        description="Evaluate whether a local repository has a reasonable foundation.",
    )
    parser.add_argument(
        "repository", nargs="?", default=".",
        help="local repository directory (default: current directory)",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    return parser


def _summary(results: Sequence[CheckResult]) -> dict[str, int]:
    return {
        "passed": sum(result.status == "pass" for result in results),
        "warnings": sum(result.status == "warning" for result in results),
        "failed": sum(result.status == "fail" for result in results),
    }


def _overall_status(summary: dict[str, int]) -> str:
    if summary["failed"]:
        return "fail"
    if summary["warnings"]:
        return "warning"
    return "pass"


def _payload(repository: Path, results: Sequence[CheckResult]) -> dict[str, object]:
    summary = _summary(results)
    return {
        "repository": str(repository),
        "status": _overall_status(summary),
        "summary": summary,
        "checks": [result.to_dict() for result in results],
    }


def render_text(
    repository: Path, results: Sequence[CheckResult], stream: TextIO
) -> None:
    stream.write(f"Foundry Check: {repository}\n\n")
    labels = {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}
    for result in results:
        stream.write(f"{labels[result.status]:<5} {result.display_name}\n")
        stream.write(f"      {result.message}\n")
        for detail in result.details:
            stream.write(f"      - {detail}\n")
    summary = _summary(results)
    stream.write(
        "\nSummary: "
        f"{summary['passed']} passed, "
        f"{summary['warnings']} warning, "
        f"{summary['failed']} failed\n"
    )


def render_json(
    repository: Path, results: Sequence[CheckResult], stream: TextIO
) -> None:
    json.dump(_payload(repository, results), stream, indent=2)
    stream.write("\n")


def _render_execution_error(
    repository_text: str, output_format: str, message: str, stream: TextIO
) -> None:
    if output_format == "json":
        json.dump(
            {
                "repository": repository_text,
                "status": "error",
                "summary": {"passed": 0, "warnings": 0, "failed": 0},
                "checks": [],
                "error": message,
            },
            stream,
            indent=2,
        )
        stream.write("\n")
    else:
        stream.write(f"foundry-check: error: {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repository = Path(args.repository).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        _render_execution_error(
            args.repository, args.output_format,
            "target path does not exist or is inaccessible", sys.stderr,
        )
        return 2
    if not repository.is_dir():
        _render_execution_error(
            str(repository), args.output_format,
            "target path is not a directory", sys.stderr,
        )
        return 2

    try:
        results = run_checks(repository)
        if args.output_format == "json":
            render_json(repository, results, sys.stdout)
        else:
            render_text(repository, results, sys.stdout)
    except Exception as error:  # Defensive CLI boundary; details stay concise.
        _render_execution_error(
            str(repository), args.output_format,
            f"unexpected execution error: {type(error).__name__}", sys.stderr,
        )
        return 2
    return 1 if any(result.status == "fail" for result in results) else 0
