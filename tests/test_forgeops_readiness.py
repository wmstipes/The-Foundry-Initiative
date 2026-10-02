"""Synthetic collection-to-brief regressions for readiness evidence."""

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
from forgeops.evidence import parse_evidence_json  # noqa: E402
from forgeops.evaluate import evaluate  # noqa: E402
from forgeops.incident import (  # noqa: E402
    IncidentState, build_incident_brief, parse_incident_brief_json,
    render_incident_brief_json,
)
from forgeops.models import Status  # noqa: E402
from forgeops.render import render_json  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    map_runbooks, parse_runbook_mapping_json, render_runbook_mapping_json,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402
from tests.test_forgeops_snapshot import FakeKubectl  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
TARGET = "forge-restaurant/restaurant-api"
DEPLOYMENT_ID = "deployment.forge-restaurant.restaurant-api"
POD_ID = "pod.forge-restaurant.restaurant-api-c"


class ForgeOpsReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads((ROOT / "tests/fixtures/forgeops/healthy.json").read_bytes())
        self.catalog = load_runbook_catalog(str(ROOT / "docs/reference/forgeops-runbook-catalog.json"))

    @staticmethod
    def round_trip(value, render, parse):
        output = StringIO()
        render(value, output)
        return parse(output.getvalue().encode("utf-8"))

    def collect(self, fixture, *, after=False):
        runner = FakeKubectl(fixture)
        raw = Collector(runner).collect()
        raw = replace(raw, collected_at_utc=(
            "2026-10-02T00:01:00Z" if after else "2026-10-02T00:00:00Z"
        ))
        evidence = self.round_trip(evaluate(raw), render_json, parse_evidence_json)
        return raw, evidence, runner.calls

    def brief(self, before, after):
        comparison = self.round_trip(
            compare_evidence(before, after), render_comparison_json, parse_comparison_json,
        )
        mapping = self.round_trip(
            map_runbooks(comparison, self.catalog), render_runbook_mapping_json,
            parse_runbook_mapping_json,
        )
        brief = self.round_trip(
            build_incident_brief(comparison, mapping), render_incident_brief_json,
            parse_incident_brief_json,
        )
        return mapping, brief

    def assert_transition(self, fixture, check_id, status, category=None):
        _, before, before_calls = self.collect(self.fixture)
        _, after, after_calls = self.collect(fixture, after=True)
        check = next(c for c in after.snapshot.checks if c.check_id == check_id)
        self.assertEqual(status, check.status)
        self.assertEqual(category, check.error_category)
        self.assertEqual(2 if status is Status.UNKNOWN else 1, after.snapshot.exit_code)
        self.assertEqual(before_calls, after_calls)
        mapping, brief = self.brief(before, after)
        self.assertEqual(
            IncidentState.INCOMPLETE if status is Status.UNKNOWN else IncidentState.DEGRADED,
            brief.state,
        )
        self.assertEqual([check_id], [fact.check_id for fact in brief.facts])
        self.assertEqual((), mapping.unmapped_delta_ids)
        self.assertIn("cause-not-established", brief.uncertainties)
        return check

    def test_normalization_retains_only_required_readiness_fields(self) -> None:
        fixture = deepcopy(self.fixture)
        pod = fixture["pods"][TARGET]["items"][0]
        pod["status"]["conditions"].append({"type": "CustomReady", "status": "True"})
        pod["status"]["conditions"][0].update(reason="private-reason", message="private-message")
        raw, evidence, _ = self.collect(fixture)
        by_id = {item.evidence_id: item.value for item in raw.evidence}
        deployment = by_id[DEPLOYMENT_ID]
        self.assertEqual(1, deployment["metadata"]["generation"])
        self.assertEqual(1, deployment["status"]["observedGeneration"])
        self.assertEqual(
            [{"type": "Ready", "status": "True"}],
            by_id["pods.forge-restaurant.restaurant-api"]["items"][0]["status"]["conditions"],
        )
        self.assertNotIn("private-", repr(raw))
        self.assertEqual(0, evidence.snapshot.exit_code)

    def test_pod_condition_and_container_readiness_both_gate_pass(self) -> None:
        for pod_ready, container_ready in (("False", True), ("True", False), ("False", False)):
            with self.subTest(pod_ready=pod_ready, container_ready=container_ready):
                fixture = deepcopy(self.fixture)
                state = fixture["pods"][TARGET]["items"][0]["status"]
                state["conditions"][0]["status"] = pod_ready
                state["containerStatuses"][0]["ready"] = container_ready
                check = self.assert_transition(fixture, POD_ID, Status.FAIL)
                self.assertIn(f"podReady={pod_ready}", check.observed)
                self.assertIn(f"ready={str(container_ready).lower()}", check.observed)

    def test_pod_unknown_or_malformed_ready_values_remain_unknown(self) -> None:
        for value in ("Unknown", None, True, False, 1, "true", "", {}, []):
            with self.subTest(value=value):
                fixture = deepcopy(self.fixture)
                fixture["pods"][TARGET]["items"][0]["status"]["conditions"][0]["status"] = value
                self.assert_transition(
                    fixture, POD_ID, Status.UNKNOWN,
                    "condition-unknown" if value == "Unknown" else "unexpected-shape",
                )

    def test_pod_missing_duplicate_or_malformed_conditions_remain_unknown(self) -> None:
        for conditions in (
            [], [{"type": "ContainersReady", "status": "True"}],
            [{"type": "Ready", "status": "True"}, {"type": "Ready", "status": "False"}],
            None, {}, "True", [None],
        ):
            with self.subTest(conditions=conditions):
                fixture = deepcopy(self.fixture)
                fixture["pods"][TARGET]["items"][0]["status"]["conditions"] = conditions
                self.assert_transition(
                    fixture, POD_ID, Status.UNKNOWN,
                    "incomplete-evidence" if isinstance(conditions, list) else "unexpected-shape",
                )
        fixture = deepcopy(self.fixture)
        del fixture["pods"][TARGET]["items"][0]["status"]["conditions"]
        self.assert_transition(fixture, POD_ID, Status.UNKNOWN, "incomplete-evidence")

    def test_pod_unknown_takes_precedence_over_runtime_mismatch(self) -> None:
        fixture = deepcopy(self.fixture)
        state = fixture["pods"][TARGET]["items"][0]["status"]
        state["conditions"][0]["status"] = "Unknown"
        state["containerStatuses"][0]["ready"] = False
        self.assert_transition(fixture, POD_ID, Status.UNKNOWN, "condition-unknown")

    def test_stale_deployment_generation_is_incomplete_even_with_matching_counts(self) -> None:
        for observed in (0, 1):
            with self.subTest(observed=observed):
                fixture = deepcopy(self.fixture)
                deployment = fixture["deployments"][TARGET]
                deployment["metadata"]["generation"] = 2
                deployment["status"]["observedGeneration"] = observed
                check = self.assert_transition(fixture, DEPLOYMENT_ID, Status.UNKNOWN, "stale-generation")
                self.assertIn("generation=2", check.observed)
                self.assertIn(f"observedGeneration={observed}", check.observed)

    def test_missing_or_malformed_deployment_generations_remain_unknown(self) -> None:
        for parent, key in (("metadata", "generation"), ("status", "observedGeneration")):
            for value in (None, True, False, -1, 1.0, "1", {}, []):
                with self.subTest(key=key, value=value):
                    fixture = deepcopy(self.fixture)
                    fixture["deployments"][TARGET][parent][key] = value
                    self.assert_transition(fixture, DEPLOYMENT_ID, Status.UNKNOWN, "unexpected-shape")
            fixture = deepcopy(self.fixture)
            del fixture["deployments"][TARGET][parent][key]
            self.assert_transition(fixture, DEPLOYMENT_ID, Status.UNKNOWN, "unexpected-shape")
        fixture = deepcopy(self.fixture)
        fixture["deployments"][TARGET]["metadata"]["generation"] = 0
        self.assert_transition(fixture, DEPLOYMENT_ID, Status.UNKNOWN, "unexpected-shape")

    def test_future_observed_generation_is_inconsistent_evidence(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["deployments"][TARGET]["status"]["observedGeneration"] = 2
        self.assert_transition(fixture, DEPLOYMENT_ID, Status.UNKNOWN, "inconsistent-generation")

    def test_current_generation_still_checks_replicas_and_images(self) -> None:
        for mutation in ("count", "image"):
            with self.subTest(mutation=mutation):
                fixture = deepcopy(self.fixture)
                deployment = fixture["deployments"][TARGET]
                deployment["metadata"]["generation"] = 7
                deployment["status"]["observedGeneration"] = 7
                if mutation == "count":
                    deployment["status"]["readyReplicas"] = 2
                else:
                    deployment["spec"]["template"]["spec"]["containers"][0]["image"] = "wrong:image"
                self.assert_transition(fixture, DEPLOYMENT_ID, Status.FAIL)

    def test_current_generation_can_pass_after_controller_catches_up(self) -> None:
        fixture = deepcopy(self.fixture)
        deployment = fixture["deployments"][TARGET]
        deployment["metadata"]["generation"] = 7
        deployment["status"]["observedGeneration"] = 7
        _, evidence, _ = self.collect(fixture)
        self.assertEqual(0, evidence.snapshot.exit_code)
        check = next(c for c in evidence.snapshot.checks if c.check_id == DEPLOYMENT_ID)
        self.assertEqual(Status.PASS, check.status)
        self.assertIn("generation=7, observedGeneration=7", check.observed)

    def test_malformed_replica_counts_cannot_masquerade_as_one(self) -> None:
        target = "forge-observability/prometheus"
        for parent, key in (
            ("spec", "replicas"), ("status", "updatedReplicas"),
            ("status", "readyReplicas"), ("status", "availableReplicas"),
        ):
            for value in (True, False, -1, 1.0, "1", None):
                with self.subTest(key=key, value=value):
                    fixture = deepcopy(self.fixture)
                    fixture["deployments"][target][parent][key] = value
                    self.assert_transition(
                        fixture, "deployment.forge-observability.prometheus",
                        Status.UNKNOWN, "unexpected-shape",
                    )

    def test_each_workload_requires_current_generation_and_pod_ready(self) -> None:
        for target in self.fixture["deployments"]:
            with self.subTest(target=target):
                fixture = deepcopy(self.fixture)
                del fixture["deployments"][target]["metadata"]["generation"]
                self.assert_transition(
                    fixture, "deployment." + target.replace("/", "."), Status.UNKNOWN, "unexpected-shape",
                )
                fixture = deepcopy(self.fixture)
                pod = fixture["pods"][target]["items"][0]
                pod["status"]["conditions"][0]["status"] = "False"
                check_id = "pod." + target.split("/")[0] + "." + pod["metadata"]["name"]
                self.assert_transition(fixture, check_id, Status.FAIL)

    def test_simultaneous_readiness_failure_and_stale_deployment_retain_both_facts(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["pods"][TARGET]["items"][0]["status"]["conditions"][0]["status"] = "False"
        fixture["deployments"][TARGET]["metadata"]["generation"] = 2
        _, before, _ = self.collect(self.fixture)
        _, after, _ = self.collect(fixture, after=True)
        mapping, brief = self.brief(before, after)
        self.assertEqual(Status.UNKNOWN, after.snapshot.overall_status)
        self.assertEqual(IncidentState.INCOMPLETE, brief.state)
        self.assertEqual(
            {DEPLOYMENT_ID: Status.UNKNOWN, POD_ID: Status.FAIL},
            {fact.check_id: fact.after_status for fact in brief.facts},
        )
        self.assertEqual((), mapping.unmapped_delta_ids)


if __name__ == "__main__":
    unittest.main()
