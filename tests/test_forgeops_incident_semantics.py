"""Exercise incident meaning through collected and serialized evidence, offline."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.collect import Collector  # noqa: E402
from forgeops.comparison import (  # noqa: E402
    compare_evidence, parse_comparison_json, render_comparison_json,
)
from forgeops.constants import RESTAURANT_ENDPOINTS  # noqa: E402
from forgeops.evidence import parse_evidence_json  # noqa: E402
from forgeops.evaluate import evaluate  # noqa: E402
from forgeops.incident import (  # noqa: E402
    IncidentState, build_incident_brief, parse_incident_brief_json,
    render_incident_brief_json, render_incident_brief_text,
)
from forgeops.models import Status  # noqa: E402
from forgeops.render import render_json  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    map_runbooks, parse_runbook_mapping_json, render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402
from forgeops.runners import HttpResponse, RunnerFailure  # noqa: E402
from tests.test_forgeops_snapshot import FakeHttp, FakeKubectl  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "forgeops"


class FaultHttp(FakeHttp):
    def __init__(self, fixture: dict, path: str, mode: str) -> None:
        super().__init__(fixture)
        self.path = path
        self.mode = mode

    def get(self, base_url: str, path: str) -> HttpResponse:
        if path != self.path:
            return super().get(base_url, path)
        if self.mode == "timeout":
            raise RunnerFailure("timeout", "synthetic request timed out")
        if self.mode == "non-json-503":
            return HttpResponse(503, b"upstream unavailable")
        return HttpResponse(503, super().get(base_url, path).body)


class ForgeOpsIncidentSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kubernetes = json.loads((FIXTURES / "healthy.json").read_bytes())
        self.http = json.loads((FIXTURES / "http.json").read_bytes())
        self.catalog = load_runbook_catalog(str(
            ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json",
        ))

    @staticmethod
    def round_trip(value, render, parse):
        output = StringIO()
        render(value, output)
        return parse(output.getvalue().encode("utf-8"))

    def collect(self, fixture=None, http=None, *, after=False, include_http=True):
        raw = Collector(
            FakeKubectl(self.kubernetes if fixture is None else fixture),
            FakeHttp(self.http) if http is None else http,
        ).collect("http://192.0.2.10:30080" if include_http else None)
        raw = replace(raw, collected_at_utc=(
            "2026-10-02T00:01:00Z" if after else "2026-10-02T00:00:00Z"
        ))
        return self.round_trip(evaluate(raw), render_json, parse_evidence_json)

    def brief(self, before, after):
        comparison = self.round_trip(
            compare_evidence(before, after), render_comparison_json,
            parse_comparison_json,
        )
        mapping = self.round_trip(
            map_runbooks(comparison, self.catalog), render_runbook_mapping_json,
            parse_runbook_mapping_json,
        )
        brief = self.round_trip(
            build_incident_brief(comparison, mapping), render_incident_brief_json,
            parse_incident_brief_json,
        )
        text = StringIO()
        render_incident_brief_text(brief, text)
        return comparison, mapping, brief, text.getvalue()

    def test_kubernetes_conditions_preserve_unknown_through_the_brief(self) -> None:
        before = self.collect()
        for family in ("node", "metrics"):
            for condition in ("Unknown", None, "unexpected", True, False, {}, []):
                with self.subTest(family=family, condition=condition):
                    fixture = deepcopy(self.kubernetes)
                    if family == "node":
                        resource = fixture["nodes"]["items"][0]
                        check_id = "node." + resource["metadata"]["name"]
                        runbook_id = "node-readiness"
                    else:
                        resource = fixture["metrics"]
                        check_id = "metrics-api-service"
                        runbook_id = "metrics-api-investigation"
                    resource["status"]["conditions"][0]["status"] = condition
                    after = self.collect(fixture, after=True)
                    check = next(c for c in after.snapshot.checks if c.check_id == check_id)
                    self.assertEqual(Status.UNKNOWN, check.status)
                    self.assertEqual(
                        "condition-unknown" if condition == "Unknown" else "unexpected-shape",
                        check.error_category,
                    )
                    self.assertEqual(2, after.snapshot.exit_code)
                    _, mapping, brief, _ = self.brief(before, after)
                    self.assertEqual(IncidentState.INCOMPLETE, brief.state)
                    self.assertIn("evidence-incomplete", brief.uncertainties)
                    self.assertEqual([runbook_id], [m.runbook_id for m in mapping.matches])

    def test_restaurant_http_failures_and_collection_gaps_map_real_ids(self) -> None:
        before = self.collect()
        for path in RESTAURANT_ENDPOINTS:
            for mode in ("json-503", "non-json-503", "timeout"):
                with self.subTest(path=path, mode=mode):
                    after = self.collect(http=FaultHttp(self.http, path, mode), after=True)
                    _, mapping, brief, text = self.brief(before, after)
                    self.assertEqual((), mapping.unmapped_delta_ids)
                    self.assertEqual(["restaurant-endpoint"], [m.runbook_id for m in mapping.matches])
                    self.assertEqual("http.restaurant-api" + path, brief.facts[0].check_id)
                    self.assertEqual(
                        IncidentState.DEGRADED if mode == "json-503" else IncidentState.INCOMPLETE,
                        brief.state,
                    )
                    self.assertIn("cause-not-established", brief.uncertainties)
                    self.assertIn("informational only", text)
                    self.assertNotIn("service-endpoints", [m.runbook_id for m in mapping.matches])

    def test_restaurant_selectors_do_not_match_lookalike_or_other_http_ids(self) -> None:
        before = self.collect()
        after = self.collect(http=FaultHttp(self.http, "/ready", "json-503"), after=True)
        comparison = compare_evidence(before, after)
        for check_id in (
            "http.restaurant-api-other/ready", "http.restaurant-api.ready",
            "http.restaurant-api/unreviewed", "http.forge-yaml-workbench/healthz",
        ):
            with self.subTest(check_id=check_id):
                changed = replace(comparison, deltas=(replace(comparison.deltas[0], check_id=check_id),))
                mapping = map_runbooks(changed, self.catalog)
                self.assertEqual((), mapping.matches)
                self.assertEqual((check_id,), mapping.unmapped_delta_ids)

    def test_unchanged_failures_and_unknowns_do_not_become_health_claims(self) -> None:
        for condition, status in (("False", Status.FAIL), ("Unknown", Status.UNKNOWN)):
            with self.subTest(condition=condition):
                fixture = deepcopy(self.kubernetes)
                fixture["metrics"]["status"]["conditions"][0]["status"] = condition
                before, after = self.collect(fixture), self.collect(fixture, after=True)
                comparison, _, brief, text = self.brief(before, after)
                self.assertEqual(status, comparison.after_overall_status)
                self.assertEqual(IncidentState.STABLE, brief.state)
                self.assertEqual((), brief.facts)
                self.assertIn("Bounded state: STABLE (deltas only)", text)
                self.assertIn("Unchanged WARN, FAIL, or UNKNOWN checks may remain", text)
                self.assertIn("source snapshot summaries", text)

    def test_partial_recovery_keeps_the_delta_only_warning_visible(self) -> None:
        for condition in ("False", "Unknown"):
            with self.subTest(condition=condition):
                fixture = deepcopy(self.kubernetes)
                fixture["metrics"]["status"]["conditions"][0]["status"] = condition
                before = self.collect(fixture, FaultHttp(self.http, "/ready", "json-503"))
                after = self.collect(fixture, after=True)
                comparison, _, brief, text = self.brief(before, after)
                self.assertIsNot(Status.PASS, comparison.after_overall_status)
                self.assertEqual(IncidentState.RECOVERED, brief.state)
                self.assertEqual(["http.restaurant-api/ready"], [f.check_id for f in brief.facts])
                self.assertIn("Bounded state: RECOVERED (deltas only)", text)
                self.assertIn("Unchanged WARN, FAIL, or UNKNOWN checks may remain", text)

    def test_uncollected_http_and_mesh_evidence_are_not_invented(self) -> None:
        before = self.collect(include_http=False)
        after = self.collect(after=True, include_http=False)
        _, mapping, brief, text = self.brief(before, after)
        self.assertFalse(any(c.check_id.startswith(("http.", "istio.")) for c in after.snapshot.checks))
        self.assertEqual(IncidentState.STABLE, brief.state)
        self.assertEqual((), mapping.matches)
        self.assertEqual((), brief.facts)
        self.assertIn("does not establish current health", text)


if __name__ == "__main__":
    unittest.main()
