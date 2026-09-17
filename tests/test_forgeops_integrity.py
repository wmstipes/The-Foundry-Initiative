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
from forgeops.evidence import load_evidence_artifact  # noqa: E402
from forgeops.integrity import (  # noqa: E402
    INTEGRITY_LIMITATION,
    INTEGRITY_RECORD_LIMIT,
    IntegrityRecordError,
    create_integrity_record,
    load_integrity_record,
    parse_integrity_record,
    render_integrity_record,
    verify_integrity,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "forgeops"
EVIDENCE = FIXTURE_ROOT / "evaluated-json-golden.json"
RECORD = FIXTURE_ROOT / "evaluated-json-golden.integrity.json"


class ForgeOpsIntegrityTests(unittest.TestCase):
    def test_commands_are_explicitly_supported(self) -> None:
        create = build_parser().parse_args([
            "evidence", "integrity", "create", "--input", "snapshot.json",
        ])
        verify = build_parser().parse_args([
            "evidence", "integrity", "verify", "--input", "snapshot.json",
            "--record", "snapshot.integrity.json",
        ])
        self.assertEqual("create", create.integrity_command)
        self.assertEqual("verify", verify.integrity_command)

    def test_record_matches_exact_golden_bytes_and_is_repeatable(self) -> None:
        artifact = load_evidence_artifact(str(EVIDENCE))
        record = create_integrity_record(artifact)
        first, second = StringIO(), StringIO()
        render_integrity_record(record, first)
        render_integrity_record(record, second)
        self.assertEqual(first.getvalue(), second.getvalue())
        self.assertEqual(RECORD.read_text(encoding="utf-8"), first.getvalue())
        value = json.loads(first.getvalue())
        self.assertEqual(1209, value["byteLength"])
        self.assertEqual([INTEGRITY_LIMITATION], value["limitations"])

    def test_valid_record_verifies_and_byte_change_mismatches(self) -> None:
        artifact = load_evidence_artifact(str(EVIDENCE))
        record = load_integrity_record(str(RECORD))
        self.assertTrue(verify_integrity(artifact, record).matches)

        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "changed.json"
            changed.write_bytes(EVIDENCE.read_bytes() + b"\n")
            changed_artifact = load_evidence_artifact(str(changed))
        verification = verify_integrity(changed_artifact, record)
        self.assertFalse(verification.matches)
        self.assertFalse(verification.byte_length_matches)
        self.assertFalse(verification.digest_matches)
        self.assertTrue(verification.metadata_matches)
        self.assertEqual(1, verification.exit_code)

    def test_strict_record_parser_rejects_unsafe_or_inconsistent_forms(self) -> None:
        original = RECORD.read_bytes()
        cases = {
            "oversized-record": b"x" * (INTEGRITY_RECORD_LIMIT + 1),
            "duplicate-key": original.replace(
                b'"schema": "forgeops.integrity/v1alpha1",',
                b'"schema": "forgeops.integrity/v1alpha1", "schema": "again",',
                1,
            ),
            "contract-digest": original.replace(b"215dc9", b"ABCDEF", 1),
            "contract-length": original.replace(b'"byteLength": 1209', b'"byteLength": true', 1),
            "unsupported-evidence-schema": original.replace(
                b"forgeops.snapshot/v1alpha1", b"forgeops.snapshot/v2", 1,
            ),
        }
        for code, raw in cases.items():
            with self.subTest(code=code), self.assertRaises(IntegrityRecordError) as caught:
                parse_integrity_record(raw)
            self.assertEqual(code, caught.exception.code)

    def test_cli_create_and_verify_have_distinct_exit_semantics(self) -> None:
        created = StringIO()
        with redirect_stdout(created):
            create_exit = main([
                "evidence", "integrity", "create", "--input", str(EVIDENCE),
            ])
        self.assertEqual(0, create_exit)
        self.assertEqual(RECORD.read_text(encoding="utf-8"), created.getvalue())

        verified = StringIO()
        with redirect_stdout(verified):
            verify_exit = main([
                "evidence", "integrity", "verify", "--input", str(EVIDENCE),
                "--record", str(RECORD),
            ])
        self.assertEqual(0, verify_exit)
        self.assertEqual(
            "MATCH forgeops.integrity/v1alpha1 length=match digest=match metadata=match\n",
            verified.getvalue(),
        )

    def test_cli_mismatch_returns_one_without_exposing_paths_or_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "private-snapshot-name.json"
            changed.write_bytes(EVIDENCE.read_bytes() + b"\n")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "evidence", "integrity", "verify", "--input", str(changed),
                    "--record", str(RECORD),
                ])
        self.assertEqual(1, exit_code)
        self.assertEqual("", errors.getvalue())
        self.assertIn("MISMATCH", output.getvalue())
        self.assertNotIn("private-snapshot-name", output.getvalue())
        self.assertNotIn("Node is Ready", output.getvalue())

    def test_cli_invalid_record_returns_two_with_no_partial_output(self) -> None:
        output, errors = StringIO(), StringIO()
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "private-record-name.json"
            record.write_text("not json", encoding="utf-8")
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "evidence", "integrity", "verify", "--input", str(EVIDENCE),
                    "--record", str(record),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("integrity record invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-record-name", errors.getvalue())

    def test_integrity_commands_do_not_construct_collection_or_network(self) -> None:
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(StringIO()):
            self.assertEqual(0, main([
                "evidence", "integrity", "verify", "--input", str(EVIDENCE),
                "--record", str(RECORD),
            ]))
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
