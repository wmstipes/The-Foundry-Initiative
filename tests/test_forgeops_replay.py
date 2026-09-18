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
    COMPARISON_INPUT_LIMIT,
    ComparisonValidationError,
    load_comparison_file,
    parse_comparison_json,
)


SCENARIO_ROOT = Path(__file__).parent / "fixtures" / "forgeops" / "scenarios"
SCENARIOS = (
    "stable-baseline",
    "pod-restart-warning",
    "routing-regression",
    "incomplete-evidence",
    "routing-recovery",
)


class ForgeOpsReplayTests(unittest.TestCase):
    @staticmethod
    def paths(name: str) -> tuple[Path, Path, Path]:
        root = SCENARIO_ROOT / name
        return (
            root / "before.json",
            root / "after.json",
            root / "expected-comparison.json",
        )

    @staticmethod
    def encoded(value: dict) -> bytes:
        return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode()

    def test_command_requires_three_explicit_inputs(self) -> None:
        args = build_parser().parse_args([
            "scenario", "replay", "--before", "before.json",
            "--after", "after.json", "--expected", "expected.json",
        ])
        self.assertEqual("scenario", args.command)
        self.assertEqual("replay", args.scenario_command)
        self.assertEqual("expected.json", args.expected)

    def test_every_curated_scenario_replays_as_an_expectation_match(self) -> None:
        for name in SCENARIOS:
            before, after, expected = self.paths(name)
            output, errors = StringIO(), StringIO()
            with self.subTest(scenario=name), redirect_stdout(output), \
                    redirect_stderr(errors):
                exit_code = main([
                    "scenario", "replay", "--before", str(before),
                    "--after", str(after), "--expected", str(expected),
                ])
            self.assertEqual(0, exit_code)
            self.assertTrue(output.getvalue().startswith(
                "MATCH forgeops.scenario-replay/v1alpha1 ",
            ))
            self.assertEqual("", errors.getvalue())

    def test_valid_recovery_comparison_exit_one_is_replay_success(self) -> None:
        before, after, expected = self.paths("routing-recovery")
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([
                "scenario", "replay", "--before", str(before),
                "--after", str(after), "--expected", str(expected),
            ])
        self.assertEqual(0, exit_code)
        self.assertIn("expectedComparisonExit=1", output.getvalue())
        self.assertIn("actualComparisonExit=1", output.getvalue())

    def test_valid_expectation_mismatch_returns_one(self) -> None:
        before, after, expected = self.paths("routing-regression")
        value = json.loads(expected.read_bytes())
        value["afterOverallStatus"] = "WARN"
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "private-expected-name.json"
            changed.write_bytes(self.encoded(value))
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "scenario", "replay", "--before", str(before),
                    "--after", str(after), "--expected", str(changed),
                ])
        self.assertEqual(1, exit_code)
        self.assertEqual("", errors.getvalue())
        self.assertIn("MISMATCH", output.getvalue())
        self.assertNotIn("private-expected-name", output.getvalue())
        self.assertNotIn("synthetic-service", output.getvalue())

    def test_expected_comparison_loader_is_strict_and_bounded(self) -> None:
        _, _, expected = self.paths("routing-regression")
        original = expected.read_bytes()
        inconsistent = json.loads(original)
        inconsistent["summary"]["changedChecks"] = 2
        duplicate = original.replace(
            b'"schema": "forgeops.comparison/v1alpha1",',
            b'"schema": "forgeops.comparison/v1alpha1", "schema": "again",',
            1,
        )
        invalid_shape = json.loads(original)
        invalid_shape["deltas"][0]["beforeStatus"] = None
        cases = {
            "oversized-input": b"x" * (COMPARISON_INPUT_LIMIT + 1),
            "duplicate-key": duplicate,
            "inconsistent-summary": self.encoded(inconsistent),
            "contract-delta": self.encoded(invalid_shape),
        }
        for code, raw in cases.items():
            with self.subTest(code=code), self.assertRaises(ComparisonValidationError) as caught:
                parse_comparison_json(raw)
            self.assertEqual(code, caught.exception.code)

    def test_invalid_expectation_returns_two_without_partial_output(self) -> None:
        before, after, _ = self.paths("stable-baseline")
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory) / "private-expected.json"
            expected.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "scenario", "replay", "--before", str(before),
                    "--after", str(after), "--expected", str(expected),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("expected comparison invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-expected", errors.getvalue())

    def test_expected_comparison_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ComparisonValidationError) as caught:
                load_comparison_file(directory)
        self.assertEqual("input-unavailable", caught.exception.code)

    def test_replay_does_not_construct_collection_or_network(self) -> None:
        before, after, expected = self.paths("incomplete-evidence")
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(StringIO()):
            self.assertEqual(0, main([
                "scenario", "replay", "--before", str(before),
                "--after", str(after), "--expected", str(expected),
            ]))
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
