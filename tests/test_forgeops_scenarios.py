from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import main  # noqa: E402
from forgeops.comparison import compare_evidence, render_comparison_json  # noqa: E402
from forgeops.evidence import EVIDENCE_INPUT_LIMIT, load_evidence_file  # noqa: E402


SCENARIO_ROOT = Path(__file__).parent / "fixtures" / "forgeops" / "scenarios"
SCENARIOS = {
    "stable-baseline": {
        "before": "PASS",
        "after": "PASS",
        "contained_after_exit": 0,
        "comparison_exit": 0,
        "delta": None,
    },
    "pod-restart-warning": {
        "before": "PASS",
        "after": "WARN",
        "contained_after_exit": 1,
        "comparison_exit": 1,
        "delta": (
            "pod.forge-restaurant.synthetic-restaurant-api",
            "STATUS_CHANGED",
            ("status", "observation", "observed"),
        ),
    },
    "routing-regression": {
        "before": "PASS",
        "after": "FAIL",
        "contained_after_exit": 1,
        "comparison_exit": 1,
        "delta": (
            "routing.forge-restaurant.synthetic-service",
            "STATUS_CHANGED",
            ("status", "observation", "observed"),
        ),
    },
    "incomplete-evidence": {
        "before": "PASS",
        "after": "UNKNOWN",
        "contained_after_exit": 2,
        "comparison_exit": 1,
        "delta": (
            "metrics-api-service",
            "STATUS_CHANGED",
            ("status", "observation", "expected", "observed", "errorCategory"),
        ),
    },
    "routing-recovery": {
        "before": "FAIL",
        "after": "PASS",
        "contained_after_exit": 0,
        "comparison_exit": 1,
        "delta": (
            "routing.forge-restaurant.synthetic-service",
            "STATUS_CHANGED",
            ("status", "observation", "observed"),
        ),
    },
}


class ForgeOpsScenarioCorpusTests(unittest.TestCase):
    def test_inventory_is_exact_and_every_artifact_is_bounded(self) -> None:
        directories = {path.name for path in SCENARIO_ROOT.iterdir() if path.is_dir()}
        self.assertEqual(set(SCENARIOS), directories)
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                files = {path.name for path in (SCENARIO_ROOT / name).iterdir()}
                self.assertEqual(
                    {"before.json", "after.json", "expected-comparison.json"},
                    files,
                )
                for filename in files:
                    self.assertLessEqual(
                        (SCENARIO_ROOT / name / filename).stat().st_size,
                        EVIDENCE_INPUT_LIMIT,
                    )

    def test_scenarios_validate_and_match_exact_comparison_documents(self) -> None:
        for name, expected in SCENARIOS.items():
            with self.subTest(scenario=name):
                directory = SCENARIO_ROOT / name
                before = load_evidence_file(str(directory / "before.json"))
                after = load_evidence_file(str(directory / "after.json"))
                comparison = compare_evidence(before, after)

                self.assertEqual(expected["before"], before.snapshot.overall_status.value)
                self.assertEqual(expected["after"], after.snapshot.overall_status.value)
                self.assertEqual(
                    expected["contained_after_exit"], after.snapshot.exit_code,
                )
                self.assertEqual(expected["comparison_exit"], comparison.exit_code)

                expected_delta = expected["delta"]
                if expected_delta is None:
                    self.assertEqual((), comparison.deltas)
                else:
                    self.assertEqual(1, len(comparison.deltas))
                    delta = comparison.deltas[0]
                    self.assertEqual(expected_delta[0], delta.check_id)
                    self.assertEqual(expected_delta[1], delta.kind.value)
                    self.assertEqual(expected_delta[2], delta.changed_fields)

                first, second = StringIO(), StringIO()
                render_comparison_json(comparison, first)
                render_comparison_json(comparison, second)
                self.assertEqual(first.getvalue(), second.getvalue())
                self.assertEqual(
                    (directory / "expected-comparison.json").read_text(
                        encoding="utf-8",
                    ),
                    first.getvalue(),
                )

    def test_existing_cli_exercises_corpus_without_collection_or_network(self) -> None:
        for name, expected in SCENARIOS.items():
            directory = SCENARIO_ROOT / name
            before_path = directory / "before.json"
            after_path = directory / "after.json"
            with self.subTest(scenario=name), \
                    mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                    mock.patch("forgeops.cli.Collector") as collector, \
                    mock.patch("forgeops.cli.HttpRunner") as http:
                for path in (before_path, after_path):
                    output, errors = StringIO(), StringIO()
                    with redirect_stdout(output), redirect_stderr(errors):
                        validation_exit = main([
                            "evidence", "validate", "--input", str(path),
                        ])
                    self.assertEqual(0, validation_exit)
                    self.assertTrue(output.getvalue().startswith("VALID "))
                    self.assertEqual("", errors.getvalue())

                output, errors = StringIO(), StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    comparison_exit = main([
                        "evidence", "compare",
                        "--before", str(before_path),
                        "--after", str(after_path),
                        "--format", "json",
                    ])
                self.assertEqual(expected["comparison_exit"], comparison_exit)
                self.assertEqual(
                    (directory / "expected-comparison.json").read_text(
                        encoding="utf-8",
                    ),
                    output.getvalue(),
                )
                self.assertEqual("", errors.getvalue())
                kubectl.assert_not_called()
                collector.assert_not_called()
                http.assert_not_called()

    def test_corpus_is_synthetic_and_disclosure_minimized(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SCENARIO_ROOT.rglob("*"))
            if path.is_file()
        )
        for forbidden in (
            "192.168.",
            "10.244.",
            "client-key-data",
            "certificate-data",
            "authorization:",
            "token=",
            '"uid"',
            '"addresses"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined.lower())
        self.assertIn("synthetic", combined.lower())
        self.assertIn("not captured signalforge evidence", combined.lower())


if __name__ == "__main__":
    unittest.main()
