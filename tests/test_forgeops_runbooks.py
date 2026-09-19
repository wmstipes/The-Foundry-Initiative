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
from forgeops.runbooks import (  # noqa: E402
    RUNBOOK_CATALOG_INPUT_LIMIT,
    RunbookCatalogError,
    load_runbook_catalog,
    parse_runbook_catalog_json,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"


class ForgeOpsRunbookCatalogTests(unittest.TestCase):
    @staticmethod
    def encoded(value: dict) -> bytes:
        return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode()

    def test_catalog_validation_command_is_explicit(self) -> None:
        args = build_parser().parse_args([
            "runbook", "catalog", "validate", "--input", "catalog.json",
        ])
        self.assertEqual("runbook", args.command)
        self.assertEqual("catalog", args.runbook_command)
        self.assertEqual("validate", args.catalog_command)
        self.assertEqual("catalog.json", args.input)

    def test_canonical_catalog_is_valid_and_deterministically_ordered(self) -> None:
        catalog = load_runbook_catalog(str(CATALOG_PATH))
        identifiers = [entry.runbook_id for entry in catalog.entries]
        self.assertEqual(sorted(identifiers), identifiers)
        self.assertEqual(7, len(catalog.entries))
        self.assertEqual(14, sum(len(entry.signals) for entry in catalog.entries))

    def test_every_catalog_target_and_section_exists(self) -> None:
        catalog = load_runbook_catalog(str(CATALOG_PATH))
        for entry in catalog.entries:
            path = ROOT / entry.path
            with self.subTest(entry=entry.runbook_id):
                self.assertTrue(path.is_file())
                headings = {
                    line.lstrip("#").strip().lstrip("\ufeff")
                    for line in path.read_text(encoding="utf-8-sig").splitlines()
                    if line.startswith("#")
                }
                self.assertIn(entry.section, headings)

    def test_catalog_loader_rejects_invalid_contracts(self) -> None:
        original = CATALOG_PATH.read_bytes()
        duplicate = original.replace(
            b'"schema": "forgeops.runbook-catalog/v1alpha1",',
            b'"schema": "forgeops.runbook-catalog/v1alpha1", "schema": "again",',
            1,
        )
        invalid_path = json.loads(original)
        invalid_path["entries"][0]["path"] = "../private.md"
        unordered = json.loads(original)
        unordered["entries"] = list(reversed(unordered["entries"]))
        cases = {
            "oversized-input": b"x" * (RUNBOOK_CATALOG_INPUT_LIMIT + 1),
            "duplicate-key": duplicate,
            "contract-path": self.encoded(invalid_path),
            "contract-order": self.encoded(unordered),
        }
        for code, raw in cases.items():
            with self.subTest(code=code), self.assertRaises(RunbookCatalogError) as caught:
                parse_runbook_catalog_json(raw)
            self.assertEqual(code, caught.exception.code)

    def test_invalid_catalog_returns_two_without_disclosing_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private-catalog-name.json"
            private.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "runbook", "catalog", "validate", "--input", str(private),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("runbook catalog invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-catalog-name", errors.getvalue())

    def test_validation_is_offline_and_constructs_no_runner(self) -> None:
        output = StringIO()
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(output):
            exit_code = main([
                "runbook", "catalog", "validate", "--input", str(CATALOG_PATH),
            ])
        self.assertEqual(0, exit_code)
        self.assertEqual(
            "VALID forgeops.runbook-catalog/v1alpha1 entries=7 signals=14\n",
            output.getvalue(),
        )
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
