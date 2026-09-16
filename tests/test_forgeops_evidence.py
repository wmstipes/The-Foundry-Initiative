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

from forgeops.cli import main  # noqa: E402
from forgeops.evidence import (  # noqa: E402
    EVIDENCE_INPUT_LIMIT,
    EvidenceValidationError,
    load_evidence_file,
    parse_evidence_json,
)
from forgeops.models import Status  # noqa: E402


FIXTURE = Path(__file__).parent / "fixtures" / "forgeops" / "evaluated-json-golden.json"


class ForgeOpsEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = FIXTURE.read_bytes()
        self.payload = json.loads(self.raw)

    @staticmethod
    def encoded(payload: dict) -> bytes:
        return (json.dumps(payload, ensure_ascii=True, indent=2) + "\n").encode()

    def assert_error(self, code: str, raw: bytes) -> None:
        with self.assertRaises(EvidenceValidationError) as caught:
            parse_evidence_json(raw)
        self.assertEqual(code, caught.exception.code)

    def test_golden_artifact_loads_as_valid_unknown_evidence(self) -> None:
        evidence = load_evidence_file(str(FIXTURE))
        self.assertEqual("forgeops.snapshot/v1alpha1", evidence.snapshot.schema)
        self.assertEqual(Status.UNKNOWN, evidence.snapshot.overall_status)
        self.assertEqual(2, evidence.snapshot.exit_code)
        self.assertEqual(2, len(evidence.snapshot.checks))

    def test_valid_unhealthy_artifact_returns_validation_success(self) -> None:
        output = StringIO()
        errors = StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            exit_code = main(["evidence", "validate", "--input", str(FIXTURE)])
        self.assertEqual(0, exit_code)
        self.assertEqual("", errors.getvalue())
        self.assertEqual(
            "VALID forgeops.snapshot/v1alpha1 checks=2 "
            "containedOverall=UNKNOWN containedExit=2\n",
            output.getvalue(),
        )

    def test_validation_does_not_invoke_collection_or_network_runners(self) -> None:
        output = StringIO()
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(output):
            exit_code = main(["evidence", "validate", "--input", str(FIXTURE)])
        self.assertEqual(0, exit_code)
        self.assertIn("containedOverall=UNKNOWN", output.getvalue())
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()

    def test_duplicate_json_key_is_rejected(self) -> None:
        duplicate = self.raw.replace(
            b'"schema": "forgeops.snapshot/v1alpha1",',
            b'"schema": "forgeops.snapshot/v1alpha1", "schema": "duplicate",',
            1,
        )
        self.assert_error("duplicate-key", duplicate)

    def test_non_utf8_and_nonstandard_numeric_constants_are_rejected(self) -> None:
        self.assert_error("invalid-utf8", b"\xff")
        altered = self.raw.replace(b'"pass": 1', b'"pass": NaN', 1)
        self.assert_error("malformed-json", altered)

    def test_oversized_input_is_rejected_before_parsing(self) -> None:
        self.assert_error("oversized-input", b"x" * (EVIDENCE_INPUT_LIMIT + 1))

    def test_unsupported_schema_is_rejected(self) -> None:
        self.payload["schema"] = "forgeops.snapshot/v2"
        self.assert_error("unsupported-schema", self.encoded(self.payload))

    def test_top_level_order_and_unexpected_check_fields_are_rejected(self) -> None:
        schema = self.payload.pop("schema")
        self.payload["schema"] = schema
        self.assert_error("contract-fields", self.encoded(self.payload))

        payload = json.loads(self.raw)
        payload["checks"][0]["unexpected"] = "value"
        self.assert_error("contract-fields", self.encoded(payload))

    def test_check_optional_field_order_is_enforced(self) -> None:
        check = self.payload["checks"][0]
        observed = check.pop("observed")
        expected = check.pop("expected")
        check["observed"] = observed
        check["expected"] = expected
        self.assert_error("contract-fields", self.encoded(self.payload))

    def test_timestamp_and_unique_check_invariants_are_enforced(self) -> None:
        self.payload["checks"][0]["collectedAtUtc"] = "2026-09-16T18:00:01Z"
        self.assert_error("contract-timestamp", self.encoded(self.payload))

        payload = json.loads(self.raw)
        payload["checks"][1]["id"] = payload["checks"][0]["id"]
        self.assert_error("duplicate-check", self.encoded(payload))

    def test_summary_counts_status_and_exit_code_are_recalculated(self) -> None:
        for field, value in (
            ("pass", 99),
            ("overallStatus", "PASS"),
            ("exitCode", 0),
        ):
            with self.subTest(field=field):
                payload = json.loads(self.raw)
                payload["summary"][field] = value
                self.assert_error("inconsistent-summary", self.encoded(payload))

    def test_boolean_summary_count_is_not_an_integer(self) -> None:
        self.payload["summary"]["pass"] = True
        self.assert_error("contract-type", self.encoded(self.payload))

    def test_missing_path_is_not_exposed_in_cli_error(self) -> None:
        secret_path = "missing-private-evidence-name.json"
        errors = StringIO()
        with redirect_stderr(errors):
            exit_code = main(["evidence", "validate", "--input", secret_path])
        self.assertEqual(2, exit_code)
        self.assertIn("input-unavailable", errors.getvalue())
        self.assertNotIn(secret_path, errors.getvalue())

    def test_directory_is_not_an_accepted_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(EvidenceValidationError) as caught:
                load_evidence_file(directory)
        self.assertEqual("input-unavailable", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
