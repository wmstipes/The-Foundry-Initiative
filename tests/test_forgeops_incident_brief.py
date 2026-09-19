from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import build_parser, main  # noqa: E402
from forgeops.comparison import (  # noqa: E402
    CheckDelta,
    DeltaKind,
    EvidenceComparison,
    load_comparison_file,
)
from forgeops.incident import (  # noqa: E402
    IncidentBriefError,
    IncidentState,
    build_incident_brief,
    classify_incident_state,
    render_incident_brief_json,
)
from forgeops.models import Status  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    RunbookMapping,
    map_runbooks,
    render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"
EVALUATION = ROOT / "tests" / "fixtures" / "forgeops" / "incident-reasoning-evaluation.json"


class ForgeOpsIncidentBriefTests(unittest.TestCase):
    def mapping_for(self, comparison: EvidenceComparison) -> RunbookMapping:
        return map_runbooks(comparison, load_runbook_catalog(str(CATALOG)))

    def write_mapping(self, path: Path, mapping: RunbookMapping) -> None:
        output = StringIO()
        render_runbook_mapping_json(mapping, output)
        path.write_text(output.getvalue(), encoding="utf-8")

    def test_command_requires_explicit_artifacts_and_json(self) -> None:
        args = build_parser().parse_args([
            "incident", "brief", "--comparison", "comparison.json",
            "--mapping", "mapping.json", "--format", "json",
        ])
        self.assertEqual("incident", args.command)
        self.assertEqual("brief", args.incident_command)
        self.assertEqual("comparison.json", args.comparison)
        self.assertEqual("mapping.json", args.mapping)
        self.assertEqual("json", args.output_format)

    def test_existing_evaluation_cases_produce_expected_states(self) -> None:
        evaluation = json.loads(EVALUATION.read_bytes())
        for case in evaluation["cases"]:
            comparison = load_comparison_file(
                str(SCENARIOS / case["scenario"] / "expected-comparison.json"),
            )
            brief = build_incident_brief(comparison, self.mapping_for(comparison))
            with self.subTest(case=case["id"]):
                self.assertEqual(case["expectedState"], brief.state.value)
                self.assertEqual(case["requiredUncertainties"], list(brief.uncertainties))
                self.assertEqual(case["expectedDeltaIds"], [fact.check_id for fact in brief.facts])
                self.assertEqual(case["expectedRunbookIds"], [item.runbook_id for item in brief.runbooks])

    def test_state_rule_is_total_for_neutral_changes(self) -> None:
        comparison = EvidenceComparison(
            schema="forgeops.snapshot/v1alpha1",
            before_collected_at_utc="2026-09-19T00:00:00Z",
            after_collected_at_utc="2026-09-19T00:01:00Z",
            before_overall_status=Status.PASS,
            after_overall_status=Status.PASS,
            total_checks=1,
            unchanged_checks=0,
            deltas=(CheckDelta(
                "synthetic.changed",
                DeltaKind.EVIDENCE_CHANGED,
                Status.PASS,
                Status.PASS,
                ("observation",),
            ),),
        )
        self.assertEqual(IncidentState.CHANGED, classify_incident_state(comparison))
        mapping = RunbookMapping(
            comparison.before_collected_at_utc,
            comparison.after_collected_at_utc,
            1,
            (),
            ("synthetic.changed",),
        )
        brief = build_incident_brief(comparison, mapping)
        self.assertEqual(
            ("cause-not-established", "mapping-incomplete", "point-in-time-only"),
            brief.uncertainties,
        )

    def test_unknown_precedes_degraded_and_recovery_requires_every_delta(self) -> None:
        base = dict(
            schema="forgeops.snapshot/v1alpha1",
            before_collected_at_utc="2026-09-19T00:00:00Z",
            after_collected_at_utc="2026-09-19T00:01:00Z",
            before_overall_status=Status.FAIL,
            after_overall_status=Status.UNKNOWN,
            total_checks=2,
            unchanged_checks=0,
        )
        mixed = EvidenceComparison(deltas=(
            CheckDelta("a", DeltaKind.STATUS_CHANGED, Status.PASS, Status.FAIL, ("status",)),
            CheckDelta("b", DeltaKind.STATUS_CHANGED, Status.PASS, Status.UNKNOWN, ("status",)),
        ), **base)
        self.assertEqual(IncidentState.INCOMPLETE, classify_incident_state(mixed))

    def test_cross_document_mismatch_fails_before_rendering(self) -> None:
        comparison = load_comparison_file(
            str(SCENARIOS / "routing-regression" / "expected-comparison.json"),
        )
        mapping = self.mapping_for(comparison)
        stale = RunbookMapping(
            "2026-09-01T00:00:00Z",
            mapping.after_collected_at_utc,
            mapping.total_deltas,
            mapping.matches,
            mapping.unmapped_delta_ids,
        )
        with self.assertRaises(IncidentBriefError) as caught:
            build_incident_brief(comparison, stale)
        self.assertEqual("window-mismatch", caught.exception.code)

    def test_json_is_repeatable_disclosure_bounded_and_process_successful(self) -> None:
        comparison_path = SCENARIOS / "incomplete-evidence" / "expected-comparison.json"
        comparison = load_comparison_file(str(comparison_path))
        with tempfile.TemporaryDirectory() as directory:
            mapping_path = Path(directory) / "mapping.json"
            self.write_mapping(mapping_path, self.mapping_for(comparison))
            first, second = StringIO(), StringIO()
            with redirect_stdout(first):
                first_exit = main([
                    "incident", "brief", "--comparison", str(comparison_path),
                    "--mapping", str(mapping_path), "--format", "json",
                ])
            with redirect_stdout(second):
                second_exit = main([
                    "incident", "brief", "--comparison", str(comparison_path),
                    "--mapping", str(mapping_path), "--format", "json",
                ])
        self.assertEqual(0, first_exit)
        self.assertEqual(0, second_exit)
        self.assertEqual(first.getvalue(), second.getvalue())
        payload = json.loads(first.getvalue())
        self.assertEqual("INCOMPLETE", payload["state"])
        self.assertNotIn("observed", first.getvalue())
        self.assertNotIn("expected", first.getvalue())
        self.assertNotIn("kubeconfig", first.getvalue())

    def test_invalid_linkage_returns_two_without_partial_output_or_paths(self) -> None:
        comparison_path = SCENARIOS / "routing-regression" / "expected-comparison.json"
        comparison = load_comparison_file(str(comparison_path))
        mapping = self.mapping_for(comparison)
        stale = RunbookMapping(
            "2026-09-01T00:00:00Z",
            mapping.after_collected_at_utc,
            mapping.total_deltas,
            mapping.matches,
            mapping.unmapped_delta_ids,
        )
        with tempfile.TemporaryDirectory() as directory:
            mapping_path = Path(directory) / "private-mapping-name.json"
            self.write_mapping(mapping_path, stale)
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "incident", "brief", "--comparison", str(comparison_path),
                    "--mapping", str(mapping_path), "--format", "json",
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("incident brief invalid: window-mismatch", errors.getvalue())
        self.assertNotIn("private-mapping-name", errors.getvalue())

    def test_incident_brief_is_offline(self) -> None:
        comparison_path = SCENARIOS / "stable-baseline" / "expected-comparison.json"
        comparison = load_comparison_file(str(comparison_path))
        with tempfile.TemporaryDirectory() as directory:
            mapping_path = Path(directory) / "mapping.json"
            self.write_mapping(mapping_path, self.mapping_for(comparison))
            with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                    mock.patch("forgeops.cli.Collector") as collector, \
                    mock.patch("forgeops.cli.HttpRunner") as http, \
                    redirect_stdout(StringIO()):
                self.assertEqual(0, main([
                    "incident", "brief", "--comparison", str(comparison_path),
                    "--mapping", str(mapping_path), "--format", "json",
                ]))
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
