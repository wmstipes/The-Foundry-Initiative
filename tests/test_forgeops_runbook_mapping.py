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
from forgeops.models import Status  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    map_runbooks,
    render_runbook_mapping_json,
    render_runbook_mapping_text,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"


class ForgeOpsRunbookMappingTests(unittest.TestCase):
    def mapping(self, scenario: str):
        comparison = load_comparison_file(
            str(SCENARIOS / scenario / "expected-comparison.json"),
        )
        catalog = load_runbook_catalog(str(CATALOG))
        return map_runbooks(comparison, catalog)

    def test_map_command_requires_explicit_inputs_and_format(self) -> None:
        args = build_parser().parse_args([
            "runbook", "map", "--comparison", "comparison.json",
            "--catalog", "catalog.json", "--format", "json",
        ])
        self.assertEqual("runbook", args.command)
        self.assertEqual("map", args.runbook_command)
        self.assertEqual("comparison.json", args.comparison)
        self.assertEqual("catalog.json", args.catalog)
        self.assertEqual("json", args.output_format)

    def test_curated_changes_map_to_grounded_sections(self) -> None:
        expected = {
            "pod-restart-warning": "pod-inspection",
            "routing-regression": "service-endpoints",
            "incomplete-evidence": "metrics-api-investigation",
            "routing-recovery": "success-verification",
        }
        for scenario, runbook_id in expected.items():
            with self.subTest(scenario=scenario):
                mapping = self.mapping(scenario)
                self.assertEqual(0, mapping.exit_code)
                self.assertEqual((), mapping.unmapped_delta_ids)
                self.assertEqual([runbook_id], [item.runbook_id for item in mapping.matches])

    def test_equivalent_comparison_is_complete_without_matches(self) -> None:
        mapping = self.mapping("stable-baseline")
        self.assertEqual(0, mapping.exit_code)
        self.assertEqual(0, mapping.total_deltas)
        self.assertEqual((), mapping.matches)
        self.assertEqual((), mapping.unmapped_delta_ids)

    def test_removed_delta_is_explicitly_unmapped(self) -> None:
        comparison = EvidenceComparison(
            schema="forgeops.snapshot/v1alpha1",
            before_collected_at_utc="2026-09-18T00:00:00Z",
            after_collected_at_utc="2026-09-18T00:01:00Z",
            before_overall_status=Status.FAIL,
            after_overall_status=Status.PASS,
            total_checks=1,
            unchanged_checks=0,
            deltas=(CheckDelta(
                "routing.forge-restaurant.restaurant-api",
                DeltaKind.REMOVED,
                Status.FAIL,
                None,
            ),),
        )
        mapping = map_runbooks(comparison, load_runbook_catalog(str(CATALOG)))
        self.assertEqual(1, mapping.exit_code)
        self.assertEqual(
            ("routing.forge-restaurant.restaurant-api",),
            mapping.unmapped_delta_ids,
        )
        self.assertEqual((), mapping.matches)

    def test_text_and_json_are_repeatable_and_semantically_consistent(self) -> None:
        mapping = self.mapping("routing-regression")
        text_first, text_second, json_first, json_second = (
            StringIO(), StringIO(), StringIO(), StringIO(),
        )
        render_runbook_mapping_text(mapping, text_first)
        render_runbook_mapping_text(mapping, text_second)
        render_runbook_mapping_json(mapping, json_first)
        render_runbook_mapping_json(mapping, json_second)
        self.assertEqual(text_first.getvalue(), text_second.getvalue())
        self.assertEqual(json_first.getvalue(), json_second.getvalue())
        payload = json.loads(json_first.getvalue())
        self.assertEqual("forgeops.runbook-mapping/v1alpha1", payload["schema"])
        self.assertEqual(mapping.exit_code, payload["summary"]["mappingExit"])
        self.assertEqual("service-endpoints", payload["matches"][0]["runbookId"])
        self.assertNotIn("observed", json_first.getvalue())
        self.assertNotIn("expected", json_first.getvalue())

    def test_cli_validates_both_inputs_before_rendering(self) -> None:
        valid = SCENARIOS / "routing-regression" / "expected-comparison.json"
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "private-input.json"
            invalid.write_text("not json", encoding="utf-8")
            cases = ((invalid, CATALOG, "comparison invalid"), (valid, invalid, "runbook catalog invalid"))
            for comparison, catalog, expected_error in cases:
                output, errors = StringIO(), StringIO()
                with self.subTest(expected_error=expected_error), \
                        redirect_stdout(output), redirect_stderr(errors):
                    exit_code = main([
                        "runbook", "map", "--comparison", str(comparison),
                        "--catalog", str(catalog), "--format", "json",
                    ])
                self.assertEqual(2, exit_code)
                self.assertEqual("", output.getvalue())
                self.assertIn(expected_error, errors.getvalue())
                self.assertNotIn("private-input", errors.getvalue())

    def test_mapping_cli_is_offline(self) -> None:
        comparison = SCENARIOS / "routing-regression" / "expected-comparison.json"
        output = StringIO()
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(output):
            exit_code = main([
                "runbook", "map", "--comparison", str(comparison),
                "--catalog", str(CATALOG), "--format", "json",
            ])
        self.assertEqual(0, exit_code)
        self.assertIn('"runbookId": "service-endpoints"', output.getvalue())
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
