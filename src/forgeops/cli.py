"""ForgeOps command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .collect import Collector, validate_kubeconfig
from .constants import EXPECTED_CONTEXT
from .evidence import EvidenceValidationError, load_evidence_file
from .evaluate import evaluate
from .render import render_json, render_markdown, render_text
from .runners import HttpRunner, KubectlRunner, RunnerFailure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forgeops",
        description="Collect or validate bounded SignalForge health evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot", help="collect the SignalForge snapshot")
    snapshot.add_argument("--kubeconfig", required=True, help="explicit kubeconfig file")
    snapshot.add_argument("--context", required=True, help=f"exact context ({EXPECTED_CONTEXT})")
    snapshot.add_argument("--restaurant-url", help="explicit Restaurant API base URL")
    snapshot.add_argument("--workbench-url", help="explicit Workbench base URL")
    snapshot.add_argument(
        "--format", choices=("text", "markdown", "json"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    evidence = subparsers.add_parser(
        "evidence", help="operate on an explicitly supplied offline evidence artifact",
    )
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    validate = evidence_commands.add_parser(
        "validate", help="validate a ForgeOps JSON evidence artifact",
    )
    validate.add_argument("--input", required=True, help="explicit local evidence file")
    return parser


def _fail(message: str) -> int:
    sys.stderr.write(f"forgeops: error: {message}\n")
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "evidence" and args.evidence_command == "validate":
        try:
            evidence = load_evidence_file(args.input)
        except EvidenceValidationError as exc:
            return _fail(f"evidence invalid: {exc.code}: {exc.summary}")
        snapshot = evidence.snapshot
        sys.stdout.write(
            f"VALID {snapshot.schema} checks={len(snapshot.checks)} "
            f"containedOverall={snapshot.overall_status.value} "
            f"containedExit={snapshot.exit_code}\n"
        )
        return 0
    if args.command != "snapshot":
        return _fail("unsupported command")
    if args.context != EXPECTED_CONTEXT:
        return _fail(f"context must exactly match {EXPECTED_CONTEXT}")
    try:
        kubeconfig: Path = validate_kubeconfig(args.kubeconfig)
        restaurant_url = (
            HttpRunner.validate_base_url(args.restaurant_url)
            if args.restaurant_url else None
        )
        workbench_url = (
            HttpRunner.validate_base_url(args.workbench_url)
            if args.workbench_url else None
        )
        runner = KubectlRunner(kubeconfig, args.context)
        raw = Collector(runner).collect(restaurant_url, workbench_url)
        snapshot = evaluate(raw)
        if args.output_format == "markdown":
            render_markdown(snapshot, sys.stdout)
        elif args.output_format == "json":
            render_json(snapshot, sys.stdout)
        else:
            render_text(snapshot, sys.stdout)
        return snapshot.exit_code
    except RunnerFailure as exc:
        return _fail(exc.detail.summary)
    except Exception as exc:  # Defensive CLI boundary; suppress sensitive details.
        return _fail(f"unexpected execution error: {type(exc).__name__}")
