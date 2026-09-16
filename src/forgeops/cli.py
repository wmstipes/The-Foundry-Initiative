"""ForgeOps command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .collect import Collector, validate_kubeconfig
from .constants import EXPECTED_CONTEXT
from .evaluate import evaluate
from .render import render_markdown, render_text
from .runners import HttpRunner, KubectlRunner, RunnerFailure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forgeops",
        description="Collect a bounded, read-only SignalForge health snapshot.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot", help="collect the SignalForge snapshot")
    snapshot.add_argument("--kubeconfig", required=True, help="explicit kubeconfig file")
    snapshot.add_argument("--context", required=True, help=f"exact context ({EXPECTED_CONTEXT})")
    snapshot.add_argument("--restaurant-url", help="explicit Restaurant API base URL")
    snapshot.add_argument("--workbench-url", help="explicit Workbench base URL")
    snapshot.add_argument(
        "--format", choices=("text", "markdown"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    return parser


def _fail(message: str) -> int:
    sys.stderr.write(f"forgeops: error: {message}\n")
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
        else:
            render_text(snapshot, sys.stdout)
        return snapshot.exit_code
    except RunnerFailure as exc:
        return _fail(exc.detail.summary)
    except Exception as exc:  # Defensive CLI boundary; suppress sensitive details.
        return _fail(f"unexpected execution error: {type(exc).__name__}")
