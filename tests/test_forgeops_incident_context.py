from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import main  # noqa: E402
from forgeops.collect import Collector  # noqa: E402
from forgeops.comparison import (  # noqa: E402
    compare_evidence, parse_comparison_json, render_comparison_json,
)
from forgeops.constants import EXPECTED_CONTEXT, SCHEMA_VERSION  # noqa: E402
from forgeops.evaluate import evaluate  # noqa: E402
from forgeops.evidence import parse_evidence_json, load_evidence_file  # noqa: E402
from forgeops.incident import IncidentBriefError, parse_incident_brief_json  # noqa: E402
from forgeops.incident_context import (  # noqa: E402
    SNAPSHOT_BRIEF_INPUT_LIMIT, build_snapshot_incident_brief,
    load_snapshot_brief, parse_snapshot_brief_json,
    render_snapshot_brief_json, render_snapshot_brief_text,
)
from forgeops.incident_replay import replay_snapshot_brief  # noqa: E402
from forgeops.models import CheckResult, EvaluatedSnapshot, Status  # noqa: E402
from forgeops.render import render_json  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    map_runbooks, parse_runbook_mapping_json, render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402
from forgeops.runners import HttpResponse  # noqa: E402
from tests.test_forgeops_snapshot import FakeHttp, FakeKubectl  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/forgeops"
SCENARIOS = FIXTURES / "incident-context"
BEFORE = "2026-10-03T00:00:00Z"
AFTER = "2026-10-03T00:01:00Z"
NODE = "node.forge-head"
METRICS = "metrics-api-service"
HTTP = "http.restaurant-api/ready"


def encoded(value):
    return json.dumps(value, ensure_ascii=True, indent=2).encode("utf-8")


def rendered(value, renderer):
    stream = StringIO()
    renderer(value, stream)
    return stream.getvalue()


def evidence(statuses, *, after=False, observation="synthetic observation"):
    timestamp = AFTER if after else BEFORE
    snapshot = EvaluatedSnapshot(SCHEMA_VERSION, timestamp, EXPECTED_CONTEXT, tuple(
        CheckResult(key, Status(value), observation, "synthetic source", timestamp)
        for key, value in statuses.items()
    ))
    return parse_evidence_json(rendered(snapshot, render_json).encode("utf-8"))


class ForgeOpsIncidentContextTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_runbook_catalog(str(ROOT / "docs/reference/forgeops-runbook-catalog.json"))

    def pipeline(self, before, after):
        comparison = parse_comparison_json(rendered(compare_evidence(before, after), render_comparison_json).encode())
        mapping = parse_runbook_mapping_json(rendered(map_runbooks(comparison, self.catalog), render_runbook_mapping_json).encode())
        return comparison, mapping, build_snapshot_incident_brief(before, after, comparison, mapping)

    def brief(self, before, after):
        return self.pipeline(evidence(before), evidence(after, after=True))[2]

    def document(self, brief):
        return json.loads(rendered(brief, render_snapshot_brief_json))

    def assert_invalid(self, value, code=None):
        with self.assertRaises(IncidentBriefError) as error:
            parse_snapshot_brief_json(value if isinstance(value, bytes) else encoded(value))
        if code:
            self.assertEqual(code, error.exception.code)

    def test_unchanged_failure_and_unknown_remain_visible(self):
        for status in ("WARN", "FAIL", "UNKNOWN"):
            with self.subTest(status=status):
                brief = self.brief({NODE: "PASS", METRICS: status}, {NODE: "PASS", METRICS: status})
                self.assertEqual("STABLE", brief.delta_brief.state.value)
                self.assertEqual(Status(status), brief.after.overall_status)
                self.assertEqual("NONE_ESTABLISHED", brief.assessment["recovery"])
                self.assertEqual([METRICS], brief.assessment["remainingNonPassingCheckIds"])
                self.assertEqual((), brief.delta_brief.facts)
                self.assertEqual((), brief.delta_brief.runbooks)
                text = rendered(brief, render_snapshot_brief_text)
                self.assertIn(f"After snapshot: {status}", text)
                self.assertIn(f"- {METRICS}: {status}", text)

    def test_partial_recovery_keeps_persistent_failures_and_unknowns(self):
        for status in ("WARN", "FAIL", "UNKNOWN"):
            with self.subTest(status=status):
                brief = self.brief({HTTP: "FAIL", METRICS: status}, {HTTP: "PASS", METRICS: status})
                self.assertEqual("RECOVERED", brief.delta_brief.state.value)
                self.assertEqual("PARTIAL", brief.assessment["recovery"])
                self.assertEqual([HTTP], brief.assessment["knownRecoveredCheckIds"])
                self.assertEqual([METRICS], brief.assessment["remainingNonPassingCheckIds"])
                text = rendered(brief, render_snapshot_brief_text)
                self.assertIn("Recovery: PARTIAL", text)
                self.assertIn(f"After snapshot: {status}", text)

    def test_complete_recovery_is_bounded_to_same_supplied_check_set(self):
        brief = self.brief({HTTP: "FAIL", METRICS: "WARN"}, {HTTP: "PASS", METRICS: "PASS"})
        self.assertEqual("COMPLETE_FOR_SUPPLIED_CHECKS", brief.assessment["recovery"])
        self.assertEqual(sorted([HTTP, METRICS]), brief.assessment["knownRecoveredCheckIds"])
        self.assertEqual("NOT_ESTABLISHED", brief.coverage["completeness"])
        self.assertIn("supplied checks only", rendered(brief, render_snapshot_brief_text))

    def test_regained_evidence_is_separate_from_known_recovery(self):
        for status in ("PASS", "WARN", "FAIL"):
            with self.subTest(status=status):
                brief = self.brief({METRICS: "UNKNOWN"}, {METRICS: status})
                self.assertEqual("NONE_ESTABLISHED", brief.assessment["recovery"])
                self.assertEqual([], brief.assessment["knownRecoveredCheckIds"])
                self.assertEqual([METRICS], brief.assessment["regainedEvidenceCheckIds"])
        combined = self.brief({HTTP: "FAIL", METRICS: "UNKNOWN"}, {HTTP: "PASS", METRICS: "PASS"})
        self.assertEqual([HTTP], combined.assessment["knownRecoveredCheckIds"])
        self.assertEqual([METRICS], combined.assessment["regainedEvidenceCheckIds"])

    def test_added_and_removed_checks_prevent_complete_recovery(self):
        for before, after, added, removed in (
            ({HTTP: "FAIL", NODE: "PASS"}, {HTTP: "PASS"}, [], [NODE]),
            ({HTTP: "FAIL"}, {HTTP: "PASS", NODE: "PASS"}, [NODE], []),
        ):
            with self.subTest(added=added, removed=removed):
                brief = self.brief(before, after)
                self.assertEqual("PARTIAL", brief.assessment["recovery"])
                self.assertEqual(added, brief.coverage["addedCheckIds"])
                self.assertEqual(removed, brief.coverage["removedCheckIds"])
        disappearance = self.brief({METRICS: "FAIL", NODE: "PASS"}, {NODE: "PASS"})
        self.assertEqual(Status.PASS, disappearance.after.overall_status)
        self.assertEqual("NONE_ESTABLISHED", disappearance.assessment["recovery"])
        self.assertEqual([METRICS], disappearance.coverage["removedCheckIds"])

    def test_absent_optional_evidence_never_claims_complete_coverage(self):
        brief = self.brief({NODE: "PASS"}, {NODE: "PASS"})
        self.assertEqual("NOT_ESTABLISHED", brief.coverage["completeness"])
        self.assertEqual([NODE], [c.check_id for c in brief.after.checks])
        text = rendered(brief, render_snapshot_brief_text)
        self.assertIn("absent from both snapshots are not assessed", text)
        self.assertIn("Optional HTTP and mesh/path coverage", text)
        self.assertEqual([], brief.assessment["knownRecoveredCheckIds"])

    def test_same_status_evidence_change_does_not_create_recovery(self):
        _, _, brief = self.pipeline(
            evidence({NODE: "FAIL"}, observation="old observation"),
            evidence({NODE: "FAIL"}, after=True, observation="new observation"),
        )
        self.assertEqual("EVIDENCE_CHANGED", brief.delta_brief.facts[0].delta_kind.value)
        self.assertEqual("NONE_ESTABLISHED", brief.assessment["recovery"])
        self.assertEqual([NODE], brief.assessment["remainingNonPassingCheckIds"])

    def test_collection_readiness_and_stale_generation_survive_into_context(self):
        fixture = json.loads((FIXTURES / "healthy.json").read_bytes())
        def collect(value, after=False):
            raw = replace(Collector(FakeKubectl(value)).collect(), collected_at_utc=AFTER if after else BEFORE)
            return parse_evidence_json(rendered(evaluate(raw), render_json).encode())
        before = collect(fixture)
        fixture["pods"]["forge-restaurant/restaurant-api"]["items"][0]["status"]["conditions"][0]["status"] = "False"
        fixture["deployments"]["forge-restaurant/restaurant-api"]["metadata"]["generation"] = 2
        _, _, brief = self.pipeline(before, collect(fixture, after=True))
        checks = {c.check_id: c.status for c in brief.after.checks}
        self.assertEqual(Status.FAIL, checks["pod.forge-restaurant.restaurant-api-c"])
        self.assertEqual(Status.UNKNOWN, checks["deployment.forge-restaurant.restaurant-api"])
        self.assertEqual(1, brief.after.summary["fail"])
        self.assertEqual(1, brief.after.summary["unknown"])
        self.assertEqual(Status.UNKNOWN, brief.after.overall_status)

    def test_non_json_http_remains_unknown_without_inventing_response_status(self):
        fixture = json.loads((FIXTURES / "healthy.json").read_bytes())
        http_fixture = json.loads((FIXTURES / "http.json").read_bytes())
        class ProxyFailure(FakeHttp):
            def get(self, base_url, path):
                return HttpResponse(503, b"private upstream error") if path == "/ready" else super().get(base_url, path)
        before = evidence({HTTP: "PASS"})
        raw = Collector(FakeKubectl(fixture), ProxyFailure(http_fixture)).collect("http://192.0.2.10:30080")
        raw = replace(raw, collected_at_utc=AFTER)
        after = parse_evidence_json(rendered(evaluate(raw), render_json).encode())
        _, _, brief = self.pipeline(before, after)
        self.assertEqual(Status.UNKNOWN, next(c.status for c in brief.after.checks if c.check_id == HTTP))
        output = rendered(brief, render_snapshot_brief_json)
        self.assertNotIn("private upstream", output)
        self.assertNotIn("503", output)
        self.assertIn(HTTP, brief.assessment["remainingNonPassingCheckIds"])

    def test_builder_rejects_mismatched_comparison_and_mapping(self):
        before, after = evidence({NODE: "FAIL"}), evidence({NODE: "PASS"}, after=True)
        comparison, mapping, _ = self.pipeline(before, after)
        mutations = (
            replace(comparison, before_overall_status=Status.PASS),
            replace(comparison, total_checks=2, unchanged_checks=1),
            replace(comparison, deltas=(replace(comparison.deltas[0], changed_fields=("status", "source")),)),
            replace(comparison, before_collected_at_utc="2026-10-02T00:00:00Z"),
        )
        for changed in mutations:
            with self.subTest(changed=changed), self.assertRaisesRegex(IncidentBriefError, "comparison does not match"):
                build_snapshot_incident_brief(before, after, changed, mapping)
        with self.assertRaises(IncidentBriefError):
            build_snapshot_incident_brief(before, after, comparison, replace(mapping, total_deltas=0))
        with self.assertRaises(IncidentBriefError):
            build_snapshot_incident_brief(before, after, comparison, replace(mapping, before_collected_at_utc=AFTER))

    def test_serialization_is_deterministic_and_omits_raw_observations(self):
        before = evidence({NODE: "FAIL", METRICS: "UNKNOWN"}, observation="private observation")
        after = evidence({METRICS: "UNKNOWN", NODE: "FAIL"}, after=True, observation="private observation")
        _, _, brief = self.pipeline(before, after)
        output = rendered(brief, render_snapshot_brief_json)
        self.assertNotIn("private observation", output)
        self.assertNotIn("synthetic source", output)
        self.assertEqual(brief, parse_snapshot_brief_json(output.encode()))
        self.assertEqual(output, rendered(parse_snapshot_brief_json(output.encode()), render_snapshot_brief_json))
        self.assertEqual(sorted([NODE, METRICS]), [c.check_id for c in brief.before.checks])

    def test_parser_rejects_tampered_summary_assessment_and_coverage(self):
        original = self.document(self.brief({NODE: "FAIL", METRICS: "UNKNOWN"}, {NODE: "PASS", METRICS: "UNKNOWN"}))
        for field, value, code in (
            ("recovery", "COMPLETE_FOR_SUPPLIED_CHECKS", "inconsistent-assessment"),
            ("knownRecoveredCheckIds", [], "inconsistent-assessment"),
            ("regainedEvidenceCheckIds", [METRICS], "inconsistent-assessment"),
            ("remainingNonPassingCheckIds", [], "inconsistent-assessment"),
        ):
            with self.subTest(field=field):
                changed = deepcopy(original)
                changed["assessment"][field] = value
                self.assert_invalid(changed, code)
        for field, value in (("completeness", "COMPLETE"), ("addedCheckIds", [NODE]), ("removedCheckIds", [METRICS]), ("limitations", [])):
            with self.subTest(field=field):
                changed = deepcopy(original)
                changed["coverage"][field] = value
                self.assert_invalid(changed, "inconsistent-coverage")
        for value in (True, 1.0, "1", -1, 2):
            with self.subTest(count=value):
                changed = deepcopy(original)
                changed["after"]["summary"]["pass"] = value
                self.assert_invalid(changed, "inconsistent-summary")

    def test_parser_rejects_wrong_types_order_duplicates_and_versions(self):
        original = self.document(self.brief({NODE: "PASS", METRICS: "FAIL"}, {NODE: "PASS", METRICS: "FAIL"}))
        mutations = []
        for field in ("schema", "evidenceSchema"):
            changed = deepcopy(original)
            changed[field] = "unsupported/v99"
            mutations.append(changed)
        for checks in ([], None, {}, [{"id": NODE, "status": True}], list(reversed(original["after"]["checks"])), original["after"]["checks"] * 2):
            changed = deepcopy(original)
            changed["after"]["checks"] = checks
            mutations.append(changed)
        changed = deepcopy(original)
        changed["unexpected"] = "field"
        mutations.append(changed)
        changed = deepcopy(original)
        changed["before"]["collectedAtUtc"] = AFTER
        mutations.append(changed)
        changed = deepcopy(original)
        changed["after"]["checks"][0]["private"] = "value"
        mutations.append(changed)
        mutations.append(dict(reversed(list(original.items()))))
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assert_invalid(changed)

    def test_parser_rejects_missing_status_facts_and_unrelated_facts(self):
        stable = self.document(self.brief({NODE: "FAIL"}, {NODE: "FAIL"}))
        changed = deepcopy(stable)
        changed["after"]["checks"][0]["status"] = "PASS"
        changed["after"]["summary"] = {"pass": 1, "warn": 0, "fail": 0, "unknown": 0, "overallStatus": "PASS", "exitCode": 0}
        self.assert_invalid(changed, "context-mismatch")
        transition = self.document(self.brief({NODE: "FAIL"}, {NODE: "PASS"}))
        changed = deepcopy(stable)
        changed["deltaBrief"] = transition["deltaBrief"]
        self.assert_invalid(changed, "context-mismatch")
        unrelated = self.document(self.brief({HTTP: "FAIL"}, {HTTP: "PASS"}))
        transition["deltaBrief"] = unrelated["deltaBrief"]
        self.assert_invalid(transition, "context-mismatch")

    def test_parser_rejects_malformed_bounded_inputs_and_nested_legacy_tampering(self):
        valid = rendered(self.brief({NODE: "PASS"}, {NODE: "PASS"}), render_snapshot_brief_json).encode()
        for raw in (b"\xff", b"not json", b"[]", b'{"x":NaN}', b'{"x":' + b"9" * 5000 + b"}",
                    b"[" * 2000 + b"]" * 2000, b"x" * (SNAPSHOT_BRIEF_INPUT_LIMIT + 1),
                    valid.replace(b'"completeness":', b'"completeness": "OTHER", "completeness":', 1)):
            with self.subTest(prefix=raw[:30]):
                self.assert_invalid(raw)
        value = json.loads(valid)
        value["deltaBrief"]["state"] = "RECOVERED"
        self.assert_invalid(value, "inconsistent-state")

    def test_replay_compares_unchanged_snapshot_context(self):
        actual = self.brief({NODE: "FAIL"}, {NODE: "FAIL"})
        expected = self.brief({NODE: "PASS"}, {NODE: "PASS"})
        self.assertEqual(actual.delta_brief, expected.delta_brief)
        output = StringIO()
        self.assertEqual(1, replay_snapshot_brief(actual, expected, output))
        self.assertIn("expectedOverall=PASS actualOverall=FAIL", output.getvalue())
        self.assertEqual(0, replay_snapshot_brief(actual, actual, StringIO()))

    def test_cli_requires_both_snapshots_and_explicit_opt_in(self):
        base = ["incident", "brief", "--comparison", "private-comparison", "--mapping", "private-mapping"]
        for extra in (["--before", "private-before"], ["--brief-version", "v1alpha2"],
                      ["--brief-version", "v1alpha2", "--after", "private-after"]):
            output, errors = StringIO(), StringIO()
            with mock.patch("forgeops.cli.load_comparison_file") as loader, redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(2, main(base + extra))
            loader.assert_not_called()
            self.assertEqual("", output.getvalue())
            self.assertNotIn("private-", errors.getvalue())

    def write_inputs(self, folder, before, after):
        comparison, mapping, brief = self.pipeline(before, after)
        for name, value, renderer in (
            ("before", before.snapshot, render_json), ("after", after.snapshot, render_json),
            ("comparison", comparison, render_comparison_json), ("mapping", mapping, render_runbook_mapping_json),
            ("expected", brief, render_snapshot_brief_json),
        ):
            (folder / f"{name}.json").write_text(rendered(value, renderer), encoding="utf-8")
        return brief

    def cli_args(self, folder, command="brief"):
        args = ["incident", command, "--brief-version", "v1alpha2"]
        for key in ("before", "after", "comparison", "mapping"):
            args += ["--" + key, str(folder / f"{key}.json")]
        if command == "replay":
            args += ["--expected", str(folder / "expected.json")]
        return args

    def test_cli_outputs_and_replay_are_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            brief = self.write_inputs(folder, evidence({NODE: "FAIL"}), evidence({NODE: "FAIL"}, after=True))
            for mode in ("text", "json", "replay"):
                with self.subTest(mode=mode):
                    args = self.cli_args(folder, "replay" if mode == "replay" else "brief")
                    if mode != "replay":
                        args += ["--format", mode]
                    output, errors = StringIO(), StringIO()
                    with mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                            mock.patch("forgeops.cli.Collector") as collector, mock.patch("forgeops.cli.HttpRunner") as http, \
                            redirect_stdout(output), redirect_stderr(errors):
                        self.assertEqual(0, main(args))
                    kubectl.assert_not_called()
                    collector.assert_not_called()
                    http.assert_not_called()
                    self.assertEqual("", errors.getvalue())
                    if mode == "json":
                        self.assertEqual(brief, parse_snapshot_brief_json(output.getvalue().encode()))
                    elif mode == "text":
                        self.assertEqual(rendered(brief, render_snapshot_brief_text), output.getvalue())
                    else:
                        self.assertIn("MATCH forgeops.incident-replay/v1alpha2", output.getvalue())

    def test_cli_mismatches_invalid_files_and_cross_version_replay_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.write_inputs(folder, evidence({NODE: "FAIL"}), evidence({NODE: "FAIL"}, after=True))
            args = self.cli_args(folder, "replay")
            (folder / "expected.json").write_text(rendered(self.brief({NODE: "PASS"}, {NODE: "PASS"}), render_snapshot_brief_json), encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main(args))
            self.assertTrue(output.getvalue().startswith("MISMATCH "))
            for raw in (b"private malformed content", (FIXTURES / "scenarios/stable-baseline/expected-incident-brief.json").read_bytes()):
                (folder / "expected.json").write_bytes(raw)
                output, errors = StringIO(), StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(2, main(args))
                self.assertEqual("", output.getvalue())
                self.assertNotIn("private", errors.getvalue())
            (folder / "after.json").write_bytes(b"private malformed snapshot")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(2, main(self.cli_args(folder)))
            self.assertEqual("", output.getvalue())
            self.assertNotIn(directory, errors.getvalue())
            self.assertNotIn("private malformed", errors.getvalue())

    def test_large_valid_snapshots_fail_before_emitting_an_oversized_brief(self):
        key = "synthetic." + "x" * 540000
        before, after = evidence({key: "PASS"}), evidence({key: "PASS"}, after=True)
        comparison = compare_evidence(before, after)
        mapping = map_runbooks(comparison, self.catalog)
        with self.assertRaises(IncidentBriefError) as error:
            build_snapshot_incident_brief(before, after, comparison, mapping)
        self.assertEqual("oversized-input", error.exception.code)

    def test_cli_rejects_inconsistent_and_reversed_source_windows_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.write_inputs(folder, evidence({NODE: "FAIL"}), evidence({NODE: "PASS"}, after=True))
            original = (folder / "before.json").read_bytes()
            for before in (evidence({NODE: "PASS"}), evidence({NODE: "FAIL"}, after=True)):
                (folder / "before.json").write_text(rendered(before.snapshot, render_json), encoding="utf-8")
                output, errors = StringIO(), StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(2, main(self.cli_args(folder)))
                self.assertEqual("", output.getvalue())
                self.assertNotIn(directory, errors.getvalue())
            (folder / "before.json").write_bytes(original)
            (folder / "after.json").write_text(rendered(evidence({NODE: "PASS"}).snapshot, render_json).replace(BEFORE, "2026-10-02T00:00:00Z"), encoding="utf-8")
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(2, main(self.cli_args(folder)))
            self.assertEqual("", output.getvalue())
            self.assertIn("reversed-chronology", errors.getvalue())
            (folder / "after.json").unlink()
            output, errors = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(2, main(self.cli_args(folder)))
            self.assertEqual("", output.getvalue())
            self.assertNotIn(directory, errors.getvalue())

    def test_versioned_goldens_and_cli_replay_match_independent_expectations(self):
        expectations = json.loads((SCENARIOS / "expectations.json").read_bytes())
        for name, expected in expectations.items():
            with self.subTest(scenario=name):
                folder = SCENARIOS / name
                before, after = load_evidence_file(str(folder / "before.json")), load_evidence_file(str(folder / "after.json"))
                _, _, brief = self.pipeline(before, after)
                self.assertEqual(expected["afterOverall"], brief.after.overall_status.value)
                self.assertEqual(expected["recovery"], brief.assessment["recovery"])
                for key in ("knownRecoveredCheckIds", "regainedEvidenceCheckIds", "remainingNonPassingCheckIds"):
                    self.assertEqual(expected[key], brief.assessment[key])
                for key in ("addedCheckIds", "removedCheckIds"):
                    self.assertEqual(expected[key], brief.coverage[key])
                self.assertEqual(expected["deltaState"], brief.delta_brief.state.value)
                self.assertEqual((folder / "expected.json").read_bytes(), rendered(brief, render_snapshot_brief_json).encode())
                self.assertEqual((folder / "expected.txt").read_text(encoding="utf-8"), rendered(brief, render_snapshot_brief_text))
                self.assertEqual(brief, load_snapshot_brief(str(folder / "expected.json")))
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(0, main(self.cli_args(folder, "replay")))
                self.assertTrue(output.getvalue().startswith("MATCH "))
                with self.assertRaises(IncidentBriefError):
                    parse_incident_brief_json((folder / "expected.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
