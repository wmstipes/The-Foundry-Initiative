from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import main  # noqa: E402
from forgeops.comparison import (  # noqa: E402
    COMPARISON_LIMITATION,
    COMPARISON_SCHEMA,
    DeltaKind,
    EvidenceComparisonError,
    compare_evidence,
    render_comparison_json,
    render_comparison_text,
)
from forgeops.evidence import parse_evidence_json  # noqa: E402


FIXTURE = Path(__file__).parent / "fixtures" / "forgeops" / "evaluated-json-golden.json"
COMPARISON_FIXTURE = (
    Path(__file__).parent / "fixtures" / "forgeops" / "comparison-json-golden.json"
)


class ForgeOpsComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(FIXTURE.read_bytes())

    @staticmethod
    def encoded(payload: dict) -> bytes:
        return (json.dumps(payload, ensure_ascii=True, indent=2) + "\n").encode()

    @staticmethod
    def set_time(payload: dict, timestamp: str) -> None:
        payload["collectedAtUtc"] = timestamp
        for check in payload["checks"]:
            check["collectedAtUtc"] = timestamp

    @staticmethod
    def recalculate(payload: dict) -> None:
        statuses = [check["status"] for check in payload["checks"]]
        for status in ("PASS", "WARN", "FAIL", "UNKNOWN"):
            payload["summary"][status.lower()] = statuses.count(status)
        if "UNKNOWN" in statuses:
            overall, exit_code = "UNKNOWN", 2
        elif "FAIL" in statuses:
            overall, exit_code = "FAIL", 1
        elif "WARN" in statuses:
            overall, exit_code = "WARN", 1
        else:
            overall, exit_code = "PASS", 0
        payload["summary"]["overallStatus"] = overall
        payload["summary"]["exitCode"] = exit_code

    def compare(self, before: dict, after: dict):
        return compare_evidence(
            parse_evidence_json(self.encoded(before)),
            parse_evidence_json(self.encoded(after)),
        )

    def test_timestamp_only_difference_is_operationally_equivalent(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        result = self.compare(before, after)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(2, result.unchanged_checks)
        self.assertEqual((), result.deltas)

    def test_status_transition_is_reported_without_health_exit_semantics(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][1]["status"] = "FAIL"
        self.recalculate(after)
        result = self.compare(before, after)
        self.assertEqual(1, result.exit_code)
        self.assertEqual("FAIL", result.after_overall_status.value)
        self.assertEqual(DeltaKind.STATUS_CHANGED, result.deltas[0].kind)
        self.assertEqual(("status",), result.deltas[0].changed_fields)

    def test_recovery_transition_is_a_difference_not_a_success_exit(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        before["checks"][1]["status"] = "FAIL"
        before["checks"][1].pop("errorCategory")
        before["checks"][1]["observation"] = "Metrics APIService is unavailable"
        before["checks"][1]["expected"] = "Available=True"
        before["checks"][1]["observed"] = "Available=False"
        self.recalculate(before)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][1]["status"] = "PASS"
        after["checks"][1].pop("errorCategory")
        after["checks"][1]["observation"] = "Metrics APIService is available"
        after["checks"][1]["expected"] = "Available=True"
        after["checks"][1]["observed"] = "Available=True"
        self.recalculate(after)
        result = self.compare(before, after)
        self.assertEqual(1, result.exit_code)
        self.assertEqual("FAIL", result.before_overall_status.value)
        self.assertEqual("PASS", result.after_overall_status.value)
        self.assertEqual(DeltaKind.STATUS_CHANGED, result.deltas[0].kind)

    def test_same_status_evidence_change_is_reported(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][0]["observed"] = "Ready=True, generation=2"
        result = self.compare(before, after)
        self.assertEqual(DeltaKind.EVIDENCE_CHANGED, result.deltas[0].kind)
        self.assertEqual(("observed",), result.deltas[0].changed_fields)

    def test_added_and_removed_checks_are_distinct_and_sorted(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"] = [deepcopy(after["checks"][0])]
        added = deepcopy(after["checks"][0])
        added["id"] = "alpha.added"
        after["checks"].append(added)
        self.recalculate(after)
        result = self.compare(before, after)
        self.assertEqual(
            ["alpha.added", "metrics-api-service"],
            [delta.check_id for delta in result.deltas],
        )
        self.assertEqual(
            [DeltaKind.ADDED, DeltaKind.REMOVED],
            [delta.kind for delta in result.deltas],
        )

    def test_reversed_chronology_fails_closed(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(before, "2026-09-16T18:05:00Z")
        with self.assertRaises(EvidenceComparisonError) as caught:
            self.compare(before, after)
        self.assertEqual("reversed-chronology", caught.exception.code)

    def test_renderer_is_stable_and_reports_explicit_counts(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][0]["observed"] = "Ready=True, generation=2"
        result = self.compare(before, after)
        first, second = StringIO(), StringIO()
        render_comparison_text(result, first)
        render_comparison_text(result, second)
        self.assertEqual(first.getvalue(), second.getvalue())
        self.assertIn("EVIDENCE_CHANGED node.forge-head", first.getvalue())
        self.assertIn("2 checks, 1 unchanged, 1 changed", first.getvalue())
        self.assertIn("comparisonExit=1", first.getvalue())

    def test_json_renderer_matches_fixed_golden_contract(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][0]["observed"] = "Ready=True, generation=2"
        result = self.compare(before, after)
        first, second = StringIO(), StringIO()
        render_comparison_json(result, first)
        render_comparison_json(result, second)
        self.assertEqual(first.getvalue(), second.getvalue())
        self.assertEqual(COMPARISON_FIXTURE.read_text(encoding="utf-8"), first.getvalue())

    def test_json_contract_has_fixed_order_and_disclosure_boundary(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")
        after["checks"][0]["observed"] = "Ready=True, generation=2"
        output = StringIO()
        render_comparison_json(self.compare(before, after), output)
        value = json.loads(output.getvalue(), object_pairs_hook=dict)
        self.assertEqual([
            "schema", "evidenceSchema", "beforeCollectedAtUtc",
            "afterCollectedAtUtc", "beforeOverallStatus", "afterOverallStatus",
            "summary", "deltas", "limitations",
        ], list(value))
        self.assertEqual(COMPARISON_SCHEMA, value["schema"])
        self.assertEqual([
            "totalChecks", "unchangedChecks", "changedChecks", "added",
            "removed", "statusChanged", "evidenceChanged", "comparisonExit",
        ], list(value["summary"]))
        self.assertEqual([
            "id", "kind", "beforeStatus", "afterStatus", "changedFields",
        ], list(value["deltas"][0]))
        self.assertEqual([COMPARISON_LIMITATION], value["limitations"])
        for forbidden in (
            "private-after-name.json", "Ready=True, generation=2",
            "kubectl get nodes -o json", "Ready=True", "Node is Ready",
        ):
            self.assertNotIn(forbidden, output.getvalue())

    def test_json_all_delta_kinds_are_sorted_with_explicit_nulls(self) -> None:
        before = deepcopy(self.payload)
        after = deepcopy(self.payload)
        self.set_time(after, "2026-09-16T18:05:00Z")

        removed = deepcopy(before["checks"][0])
        removed["id"] = "z.removed"
        before["checks"].append(removed)
        after["checks"][0]["status"] = "WARN"
        evidence_changed = deepcopy(after["checks"][1])
        evidence_changed["id"] = "m.evidence"
        evidence_changed["observation"] = "changed but still incomplete"
        before_evidence = deepcopy(before["checks"][1])
        before_evidence["id"] = "m.evidence"
        before["checks"].append(before_evidence)
        added = deepcopy(after["checks"][0])
        added["id"] = "a.added"
        after["checks"].append(evidence_changed)
        after["checks"].append(added)
        self.recalculate(before)
        self.recalculate(after)

        output = StringIO()
        render_comparison_json(self.compare(before, after), output)
        value = json.loads(output.getvalue())
        self.assertEqual(
            ["a.added", "m.evidence", "node.forge-head", "z.removed"],
            [delta["id"] for delta in value["deltas"]],
        )
        self.assertEqual(
            ["ADDED", "EVIDENCE_CHANGED", "STATUS_CHANGED", "REMOVED"],
            [delta["kind"] for delta in value["deltas"]],
        )
        self.assertIsNone(value["deltas"][0]["beforeStatus"])
        self.assertEqual([], value["deltas"][0]["changedFields"])
        self.assertIsNone(value["deltas"][-1]["afterStatus"])
        self.assertEqual([], value["deltas"][-1]["changedFields"])
        self.assertEqual({
            "totalChecks": 5,
            "unchangedChecks": 1,
            "changedChecks": 4,
            "added": 1,
            "removed": 1,
            "statusChanged": 1,
            "evidenceChanged": 1,
            "comparisonExit": 1,
        }, value["summary"])

    def test_cli_json_and_text_have_semantic_parity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before = deepcopy(self.payload)
            after = deepcopy(self.payload)
            self.set_time(after, "2026-09-16T18:05:00Z")
            after["checks"][0]["observed"] = "Ready=True, generation=2"
            before_path = Path(directory) / "before.json"
            after_path = Path(directory) / "after.json"
            before_path.write_bytes(self.encoded(before))
            after_path.write_bytes(self.encoded(after))
            text_output, json_output = StringIO(), StringIO()
            with redirect_stdout(text_output):
                text_exit = main([
                    "evidence", "compare", "--before", str(before_path),
                    "--after", str(after_path),
                ])
            with redirect_stdout(json_output):
                json_exit = main([
                    "evidence", "compare", "--before", str(before_path),
                    "--after", str(after_path), "--format", "json",
                ])
        value = json.loads(json_output.getvalue())
        self.assertEqual(1, text_exit)
        self.assertEqual(text_exit, json_exit)
        self.assertEqual("2026-09-16T18:00:00Z", value["beforeCollectedAtUtc"])
        self.assertEqual("2026-09-16T18:05:00Z", value["afterCollectedAtUtc"])
        self.assertEqual(1, value["summary"]["changedChecks"])
        self.assertEqual(1, value["summary"]["comparisonExit"])
        self.assertIn("1 changed", text_output.getvalue())

    def test_cli_invalid_json_request_emits_no_partial_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before_path = Path(directory) / "before.json"
            after_path = Path(directory) / "after.json"
            before_path.write_bytes(self.encoded(self.payload))
            after_path.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "evidence", "compare", "--before", str(before_path),
                    "--after", str(after_path), "--format", "json",
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("after evidence invalid: malformed-json", errors.getvalue())

    def test_cli_json_timestamp_only_difference_is_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before = deepcopy(self.payload)
            after = deepcopy(self.payload)
            self.set_time(after, "2026-09-16T18:05:00Z")
            before_path = Path(directory) / "before.json"
            after_path = Path(directory) / "after.json"
            before_path.write_bytes(self.encoded(before))
            after_path.write_bytes(self.encoded(after))
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main([
                    "evidence", "compare", "--before", str(before_path),
                    "--after", str(after_path), "--format", "json",
                ])
        value = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual([], value["deltas"])
        self.assertEqual(0, value["summary"]["comparisonExit"])

    def test_cli_json_reversed_chronology_emits_no_partial_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before = deepcopy(self.payload)
            after = deepcopy(self.payload)
            self.set_time(before, "2026-09-16T18:05:00Z")
            before_path = Path(directory) / "before.json"
            after_path = Path(directory) / "after.json"
            before_path.write_bytes(self.encoded(before))
            after_path.write_bytes(self.encoded(after))
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "evidence", "compare", "--before", str(before_path),
                    "--after", str(after_path), "--format", "json",
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("comparison invalid: reversed-chronology", errors.getvalue())

    def test_cli_validates_both_inputs_before_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before_path = Path(directory) / "before.json"
            after_path = Path(directory) / "private-after-name.json"
            before_path.write_bytes(self.encoded(self.payload))
            after_path.write_text("not json", encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = main([
                    "evidence", "compare",
                    "--before", str(before_path),
                    "--after", str(after_path),
                ])
        self.assertEqual(2, exit_code)
        self.assertEqual("", output.getvalue())
        self.assertIn("after evidence invalid: malformed-json", errors.getvalue())
        self.assertNotIn("private-after-name.json", errors.getvalue())

    def test_cli_comparison_does_not_invoke_collection_or_network(self) -> None:
        output = StringIO()
        with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(output):
            exit_code = main([
                "evidence", "compare",
                "--before", str(FIXTURE),
                "--after", str(FIXTURE),
            ])
        self.assertEqual(0, exit_code)
        self.assertIn("0 changed", output.getvalue())
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
