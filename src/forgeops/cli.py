"""ForgeOps command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .collect import Collector, validate_kubeconfig
from .comparison import (
    ComparisonValidationError,
    EvidenceComparisonError,
    compare_evidence,
    load_comparison_file,
    render_comparison_json,
    render_comparison_text,
)
from .constants import EXPECTED_CONTEXT
from .evidence import (
    EvidenceValidationError,
    load_evidence_artifact,
    load_evidence_file,
)
from .evaluate import evaluate
from .integrity import (
    IntegrityRecordError,
    create_integrity_record,
    load_integrity_inputs,
    render_integrity_record,
    render_integrity_verification,
    verify_integrity,
)
from .incident import (
    IncidentBriefError,
    build_incident_brief,
    load_incident_brief,
    render_incident_brief_json,
    render_incident_brief_text,
)
from .incident_replay import render_incident_replay, replay_incident_brief
from .provenance import inspect_execution_provenance, render_execution_provenance
from .replay import render_scenario_replay, replay_scenario
from .render import render_json, render_markdown, render_text
from .runbooks import RunbookCatalogError, load_runbook_catalog
from .runbook_mapping import (
    RunbookMappingError,
    load_runbook_mapping,
    map_runbooks,
    render_runbook_mapping_json,
    render_runbook_mapping_text,
)
from .runners import HttpRunner, KubectlRunner, RunnerFailure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forgeops",
        description="Inspect execution or operate on bounded SignalForge health evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "provenance", help="show the executing ForgeOps version and source",
    )
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
    compare = evidence_commands.add_parser(
        "compare", help="compare two validated ForgeOps evidence artifacts",
    )
    compare.add_argument("--before", required=True, help="explicit earlier evidence file")
    compare.add_argument("--after", required=True, help="explicit later evidence file")
    compare.add_argument(
        "--format", choices=("text", "json"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    integrity = evidence_commands.add_parser(
        "integrity", help="create or verify an exact-byte evidence integrity record",
    )
    integrity_commands = integrity.add_subparsers(
        dest="integrity_command", required=True,
    )
    integrity_create = integrity_commands.add_parser(
        "create", help="render an integrity record for validated evidence",
    )
    integrity_create.add_argument(
        "--input", required=True, help="explicit local evidence file",
    )
    integrity_verify = integrity_commands.add_parser(
        "verify", help="verify evidence against an explicit integrity record",
    )
    integrity_verify.add_argument(
        "--input", required=True, help="explicit local evidence file",
    )
    integrity_verify.add_argument(
        "--record", required=True, help="explicit local integrity-record file",
    )
    scenario = subparsers.add_parser(
        "scenario", help="operate on an explicitly supplied offline scenario",
    )
    scenario_commands = scenario.add_subparsers(
        dest="scenario_command", required=True,
    )
    replay = scenario_commands.add_parser(
        "replay", help="compare deterministic evidence with an expected comparison",
    )
    replay.add_argument("--before", required=True, help="explicit earlier evidence file")
    replay.add_argument("--after", required=True, help="explicit later evidence file")
    replay.add_argument(
        "--expected", required=True, help="explicit expected comparison file",
    )
    runbook = subparsers.add_parser(
        "runbook", help="operate on explicit offline runbook knowledge",
    )
    runbook_commands = runbook.add_subparsers(dest="runbook_command", required=True)
    catalog = runbook_commands.add_parser(
        "catalog", help="operate on a runbook catalog",
    )
    catalog_commands = catalog.add_subparsers(dest="catalog_command", required=True)
    catalog_validate = catalog_commands.add_parser(
        "validate", help="validate a ForgeOps runbook catalog",
    )
    catalog_validate.add_argument(
        "--input", required=True, help="explicit local runbook-catalog file",
    )
    mapping_artifact = runbook_commands.add_parser(
        "mapping", help="operate on a saved runbook mapping",
    )
    mapping_commands = mapping_artifact.add_subparsers(
        dest="mapping_command", required=True,
    )
    mapping_validate = mapping_commands.add_parser(
        "validate", help="validate a ForgeOps runbook mapping",
    )
    mapping_validate.add_argument(
        "--input", required=True, help="explicit local runbook-mapping file",
    )
    mapping = runbook_commands.add_parser(
        "map", help="map a validated comparison to cataloged runbook sections",
    )
    mapping.add_argument(
        "--comparison", required=True, help="explicit local comparison file",
    )
    mapping.add_argument(
        "--catalog", required=True, help="explicit local runbook-catalog file",
    )
    mapping.add_argument(
        "--format", choices=("text", "json"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    incident = subparsers.add_parser(
        "incident", help="operate on explicit offline incident artifacts",
    )
    incident_commands = incident.add_subparsers(dest="incident_command", required=True)
    brief = incident_commands.add_parser(
        "brief", help="render a deterministic artifact-bounded incident brief",
    )
    brief.add_argument(
        "--comparison", required=True, help="explicit local comparison file",
    )
    brief.add_argument(
        "--mapping", required=True, help="explicit local runbook-mapping file",
    )
    brief.add_argument(
        "--format", choices=("text", "json"), default="text",
        dest="output_format", help="output format (default: text)",
    )
    incident_replay = incident_commands.add_parser(
        "replay", help="compare a deterministic brief with an explicit expectation",
    )
    incident_replay.add_argument(
        "--comparison", required=True, help="explicit local comparison file",
    )
    incident_replay.add_argument(
        "--mapping", required=True, help="explicit local runbook-mapping file",
    )
    incident_replay.add_argument(
        "--expected", required=True, help="explicit expected incident-brief file",
    )
    return parser


def _fail(message: str) -> int:
    sys.stderr.write(f"forgeops: error: {message}\n")
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "provenance":
        provenance = inspect_execution_provenance()
        render_execution_provenance(provenance, sys.stdout)
        return provenance.exit_code
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
    if args.command == "runbook" and args.runbook_command == "map":
        try:
            comparison = load_comparison_file(args.comparison)
        except ComparisonValidationError as exc:
            return _fail(f"comparison invalid: {exc.code}: {exc.summary}")
        try:
            catalog = load_runbook_catalog(args.catalog)
        except RunbookCatalogError as exc:
            return _fail(f"runbook catalog invalid: {exc.code}: {exc.summary}")
        mapping = map_runbooks(comparison, catalog)
        if args.output_format == "json":
            render_runbook_mapping_json(mapping, sys.stdout)
        else:
            render_runbook_mapping_text(mapping, sys.stdout)
        return mapping.exit_code
    if args.command == "incident" and args.incident_command in ("brief", "replay"):
        try:
            comparison = load_comparison_file(args.comparison)
        except ComparisonValidationError as exc:
            return _fail(f"comparison invalid: {exc.code}: {exc.summary}")
        try:
            mapping = load_runbook_mapping(args.mapping)
        except RunbookMappingError as exc:
            return _fail(f"runbook mapping invalid: {exc.code}: {exc.summary}")
        try:
            brief = build_incident_brief(comparison, mapping)
        except IncidentBriefError as exc:
            return _fail(f"incident brief invalid: {exc.code}: {exc.summary}")
        if args.incident_command == "brief":
            if args.output_format == "json":
                render_incident_brief_json(brief, sys.stdout)
            else:
                render_incident_brief_text(brief, sys.stdout)
            return 0
        try:
            expected = load_incident_brief(args.expected)
        except IncidentBriefError as exc:
            return _fail(f"expected incident brief invalid: {exc.code}: {exc.summary}")
        replay = replay_incident_brief(brief, expected)
        render_incident_replay(replay, sys.stdout)
        return replay.exit_code
    if args.command == "runbook" and args.runbook_command == "mapping":
        try:
            mapping = load_runbook_mapping(args.input)
        except RunbookMappingError as exc:
            return _fail(f"runbook mapping invalid: {exc.code}: {exc.summary}")
        sys.stdout.write(
            f"VALID forgeops.runbook-mapping/v1alpha1 "
            f"totalDeltas={mapping.total_deltas} "
            f"mappedDeltas={len(mapping.mapped_delta_ids)} "
            f"unmappedDeltas={len(mapping.unmapped_delta_ids)} "
            f"runbookMatches={len(mapping.matches)} "
            f"containedMappingExit={mapping.exit_code}\n"
        )
        return 0
    if args.command == "evidence" and args.evidence_command == "compare":
        try:
            before = load_evidence_file(args.before)
        except EvidenceValidationError as exc:
            return _fail(f"before evidence invalid: {exc.code}: {exc.summary}")
        try:
            after = load_evidence_file(args.after)
        except EvidenceValidationError as exc:
            return _fail(f"after evidence invalid: {exc.code}: {exc.summary}")
        try:
            comparison = compare_evidence(before, after)
        except EvidenceComparisonError as exc:
            return _fail(f"comparison invalid: {exc.code}: {exc.summary}")
        if args.output_format == "json":
            render_comparison_json(comparison, sys.stdout)
        else:
            render_comparison_text(comparison, sys.stdout)
        return comparison.exit_code
    if args.command == "evidence" and args.evidence_command == "integrity":
        if args.integrity_command == "create":
            try:
                artifact = load_evidence_artifact(args.input)
            except EvidenceValidationError as exc:
                return _fail(f"evidence invalid: {exc.code}: {exc.summary}")
            render_integrity_record(create_integrity_record(artifact), sys.stdout)
            return 0
        if args.integrity_command == "verify":
            try:
                artifact, record = load_integrity_inputs(args.input, args.record)
            except EvidenceValidationError as exc:
                return _fail(f"evidence invalid: {exc.code}: {exc.summary}")
            except IntegrityRecordError as exc:
                return _fail(f"integrity record invalid: {exc.code}: {exc.summary}")
            verification = verify_integrity(artifact, record)
            render_integrity_verification(verification, sys.stdout)
            return verification.exit_code
    if args.command == "scenario" and args.scenario_command == "replay":
        try:
            before = load_evidence_file(args.before)
        except EvidenceValidationError as exc:
            return _fail(f"before evidence invalid: {exc.code}: {exc.summary}")
        try:
            after = load_evidence_file(args.after)
        except EvidenceValidationError as exc:
            return _fail(f"after evidence invalid: {exc.code}: {exc.summary}")
        try:
            expected = load_comparison_file(args.expected)
        except ComparisonValidationError as exc:
            return _fail(f"expected comparison invalid: {exc.code}: {exc.summary}")
        try:
            actual = compare_evidence(before, after)
        except EvidenceComparisonError as exc:
            return _fail(f"scenario invalid: {exc.code}: {exc.summary}")
        replay = replay_scenario(actual, expected)
        render_scenario_replay(replay, sys.stdout)
        return replay.exit_code
    if (
        args.command == "runbook"
        and args.runbook_command == "catalog"
        and args.catalog_command == "validate"
    ):
        try:
            catalog = load_runbook_catalog(args.input)
        except RunbookCatalogError as exc:
            return _fail(f"runbook catalog invalid: {exc.code}: {exc.summary}")
        signal_count = sum(len(entry.signals) for entry in catalog.entries)
        sys.stdout.write(
            f"VALID forgeops.runbook-catalog/v1alpha1 "
            f"entries={len(catalog.entries)} signals={signal_count}\n"
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
