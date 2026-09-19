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
from forgeops.comparison import load_comparison_file  # noqa: E402
from forgeops.incident import (  # noqa: E402
    INCIDENT_BRIEF_INPUT_LIMIT,
    IncidentBriefError,
    build_incident_brief,
    load_incident_brief,
    parse_incident_brief_json,
)
from forgeops.incident_replay import replay_incident_brief  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    map_runbooks,
    render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"
SCENARIO_NAMES = (
    "stable-baseline",
    "pod-restart-warning",
    "routing-regression",
    "incomplete-evidence",
    "routing-recovery",
)


class ForgeOpsIncidentReplayTests(unittest.TestCase):
    @staticmethod
    def encoded(value: dict) -> bytes:
        return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode()

    def write_mapping(self, path: Path, scenario: str) -> None:
        comparison = load_comparison_file(
            str(SCENARIOS / scenario / "expected-comparison.json"),
        )
        mapping = map_runbooks(comparison, load_runbook_catalog(str(CATALOG)))
        output = StringIO()
        render_runbook_mapping_json(mapping, output)
        path.write_text(output.getvalue(), encoding="utf-8")

    def test_command_requires_three_explicit_inputs(self) -> None:
        args = build_parser().parse_args([
            "incident", "replay", "--comparison", "comparison.json",
            "--mapping", "mapping.json", "--expected", "brief.json",
        ])
        self.assertEqual("incident", args.command)
        self.assertEqual("replay", args.incident_command)
        self.assertEqual("brief.json", args.expected)

    def test_expected_briefs_are_strict_and_match_production_output(self) -> None:
        catalog = load_runbook_catalog(str(CATALOG))
        for scenario in SCENARIO_NAMES:
            comparison = load_comparison_file(
                str(SCENARIOS / scenario / "expected-comparison.json"),
            )
            actual = build_incident_brief(comparison, map_runbooks(comparison, catalog))
            expected = load_incident_brief(
                str(SCENARIOS / scenario / "expected-incident-brief.json"),
            )
            with self.subTest(scenario=scenario):
                self.assertTrue(replay_incident_brief(actual, expected).matches)

    def test_every_curated_case_replays_as_a_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for scenario in SCENARIO_NAMES:
                mapping = Path(directory) / f"{scenario}-mapping.json"
                self.write_mapping(mapping, scenario)
                output, errors = StringIO(), StringIO()
                with self.subTest(scenario=scenario), redirect_stdout(output), \
                        redirect_stderr(errors):
                    exit_code = main([
                        "incident", "replay",
                        "--comparison", str(SCENARIOS / scenario / "expected-comparison.json"),
                        "--mapping", str(mapping),
                        "--expected", str(SCENARIOS / scenario / "expected-incident-brief.json"),
                    ])
                self.assertEqual(0, exit_code)
                self.assertTrue(output.getvalue().startswith(
                    "MATCH forgeops.incident-replay/v1alpha1 ",
                ))
                self.assertEqual("", errors.getvalue())

    def test_valid_expectation_mismatch_returns_one(self) -> None:
        scenario = "routing-regression"
        original = json.loads(
            (SCENARIOS / scenario / "expected-incident-brief.json").read_bytes(),
        )
        original["runbooks"][0]["title"] = "Alternate reviewed title"
        with tempfile.TemporaryDirectory() as directory:
            mapping = Path(directory) / "mapping.json"
            expected = Path(directory) / "expected.json"
            self.write_mapping(mapping, scenario)
            expected.write_bytes(self.encoded(original))
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "incident", "replay",
                    "--comparison", str(SCENARIOS / scenario / "expected-comparison.json"),
                    "--mapping", str(mapping), "--expected", str(expected),
                ])
        self.assertEqual(1, exit_code)
        self.assertIn("MISMATCH", output.getvalue())
        self.assertEqual("", errors.getvalue())
        self.assertNotIn("Alternate reviewed title", output.getvalue())

    def test_loader_rejects_invalid_briefs(self) -> None:
        path = SCENARIOS / "routing-regression" / "expected-incident-brief.json"
        original = path.read_bytes()
        duplicate = original.replace(
            b'"schema": "forgeops.incident-brief/v1alpha1",',
            b'"schema": "forgeops.incident-brief/v1alpha1", "schema": "again",',
            1,
        )
        wrong_state = json.loads(original)
        wrong_state["state"] = "STABLE"
        unsafe = json.loads(original)
        unsafe["runbooks"][0]["path"] = "../private.md"
        inconsistent = json.loads(original)
        inconsistent["unmappedDeltaIds"] = [inconsistent["facts"][0]["id"]]
        cases = {
            "oversized-input": b"x" * (INCIDENT_BRIEF_INPUT_LIMIT + 1),
            "duplicate-key": duplicate,
            "inconsistent-state": self.encoded(wrong_state),
            "contract-path": self.encoded(unsafe),
            "contract-coverage": self.encoded(inconsistent),
        }
        for code, raw in cases.items():
            with self.subTest(code=code), self.assertRaises(IncidentBriefError) as caught:
                parse_incident_brief_json(raw)
            self.assertEqual(code, caught.exception.code)

    def test_invalid_expectation_returns_two_without_partial_output_or_path(self) -> None:
        scenario = "stable-baseline"
        with tempfile.TemporaryDirectory() as directory:
            mapping = Path(directory) / "mapping.json"
            expected = Path(directory) / "private-expected-name.json"
            self.write_mapping(mapping, scenario)
            expected.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "incident", "replay",
                    "--comparison", str(SCENARIOS / scenario / "expected-comparison.json"),
                    "--mapping", str(mapping), "--expected", str(expected),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("expected incident brief invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-expected-name", errors.getvalue())

    def test_replay_is_offline(self) -> None:
        scenario = "incomplete-evidence"
        with tempfile.TemporaryDirectory() as directory:
            mapping = Path(directory) / "mapping.json"
            self.write_mapping(mapping, scenario)
            with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                    mock.patch("forgeops.cli.Collector") as collector, \
                    mock.patch("forgeops.cli.HttpRunner") as http, \
                    redirect_stdout(StringIO()):
                self.assertEqual(0, main([
                    "incident", "replay",
                    "--comparison", str(SCENARIOS / scenario / "expected-comparison.json"),
                    "--mapping", str(mapping),
                    "--expected", str(SCENARIOS / scenario / "expected-incident-brief.json"),
                ]))
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
