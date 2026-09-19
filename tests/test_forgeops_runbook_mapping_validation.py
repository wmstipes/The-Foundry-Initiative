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
from forgeops.runbook_mapping import (  # noqa: E402
    RUNBOOK_MAPPING_INPUT_LIMIT,
    RunbookMappingError,
    load_runbook_mapping,
    map_runbooks,
    parse_runbook_mapping_json,
    render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"


class ForgeOpsRunbookMappingValidationTests(unittest.TestCase):
    @staticmethod
    def encoded(value: dict) -> bytes:
        return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode()

    def mapping_bytes(self, scenario: str = "routing-regression") -> bytes:
        comparison = load_comparison_file(
            str(SCENARIOS / scenario / "expected-comparison.json"),
        )
        mapping = map_runbooks(comparison, load_runbook_catalog(str(CATALOG)))
        output = StringIO()
        render_runbook_mapping_json(mapping, output)
        return output.getvalue().encode()

    def test_validation_command_is_explicit(self) -> None:
        args = build_parser().parse_args([
            "runbook", "mapping", "validate", "--input", "mapping.json",
        ])
        self.assertEqual("runbook", args.command)
        self.assertEqual("mapping", args.runbook_command)
        self.assertEqual("validate", args.mapping_command)
        self.assertEqual("mapping.json", args.input)

    def test_current_mapping_output_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_bytes(self.mapping_bytes())
            mapping = load_runbook_mapping(str(path))
        self.assertEqual(0, mapping.exit_code)
        self.assertEqual(("service-endpoints",), tuple(item.runbook_id for item in mapping.matches))
        self.assertEqual(("routing.forge-restaurant.synthetic-service",), mapping.mapped_delta_ids)

    def test_valid_incomplete_mapping_is_contract_valid(self) -> None:
        value = json.loads(self.mapping_bytes("stable-baseline"))
        value["summary"] = {
            "totalDeltas": 1,
            "mappedDeltas": 0,
            "unmappedDeltas": 1,
            "runbookMatches": 0,
            "mappingExit": 1,
        }
        value["unmappedDeltaIds"] = ["synthetic.unmapped"]
        mapping = parse_runbook_mapping_json(self.encoded(value))
        self.assertEqual(1, mapping.exit_code)

    def test_loader_rejects_invalid_contracts(self) -> None:
        original = self.mapping_bytes()
        duplicate = original.replace(
            b'"schema": "forgeops.runbook-mapping/v1alpha1",',
            b'"schema": "forgeops.runbook-mapping/v1alpha1", "schema": "again",',
            1,
        )
        inconsistent = json.loads(original)
        inconsistent["summary"]["mappedDeltas"] = 2
        unsafe = json.loads(original)
        unsafe["matches"][0]["path"] = "../private.md"
        unordered = json.loads(original)
        unordered["unmappedDeltaIds"] = ["z", "a"]
        unordered["summary"] = {
            "totalDeltas": 3,
            "mappedDeltas": 1,
            "unmappedDeltas": 2,
            "runbookMatches": 1,
            "mappingExit": 1,
        }
        cases = {
            "oversized-input": b"x" * (RUNBOOK_MAPPING_INPUT_LIMIT + 1),
            "duplicate-key": duplicate,
            "inconsistent-summary": self.encoded(inconsistent),
            "contract-path": self.encoded(unsafe),
            "contract-order": self.encoded(unordered),
        }
        for code, raw in cases.items():
            with self.subTest(code=code), self.assertRaises(RunbookMappingError) as caught:
                parse_runbook_mapping_json(raw)
            self.assertEqual(code, caught.exception.code)

    def test_cli_validation_separates_contract_from_contained_exit(self) -> None:
        value = json.loads(self.mapping_bytes("stable-baseline"))
        value["summary"] = {
            "totalDeltas": 1,
            "mappedDeltas": 0,
            "unmappedDeltas": 1,
            "runbookMatches": 0,
            "mappingExit": 1,
        }
        value["unmappedDeltaIds"] = ["synthetic.unmapped"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_bytes(self.encoded(value))
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main([
                    "runbook", "mapping", "validate", "--input", str(path),
                ])
        self.assertEqual(0, exit_code)
        self.assertIn("containedMappingExit=1", output.getvalue())

    def test_invalid_mapping_returns_two_without_path_or_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-mapping-name.json"
            path.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "runbook", "mapping", "validate", "--input", str(path),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("runbook mapping invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-mapping-name", errors.getvalue())

    def test_validation_is_offline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_bytes(self.mapping_bytes())
            with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                    mock.patch("forgeops.cli.Collector") as collector, \
                    mock.patch("forgeops.cli.HttpRunner") as http, \
                    redirect_stdout(StringIO()):
                self.assertEqual(0, main([
                    "runbook", "mapping", "validate", "--input", str(path),
                ]))
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
