from __future__ import annotations

from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.collect import Collector  # noqa: E402
from forgeops.constants import EXPECTED_CONTEXT  # noqa: E402
from forgeops.evaluate import evaluate  # noqa: E402
from forgeops.models import CheckResult, EvaluatedSnapshot, Status  # noqa: E402
from forgeops.render import render_json, render_markdown, render_text  # noqa: E402
from forgeops.runners import HttpResponse, Operation, RunnerFailure  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures" / "forgeops"


class FakeKubectl:
    def __init__(self, fixture: dict, context: str = EXPECTED_CONTEXT) -> None:
        self.fixture = fixture
        self.context = context
        self.calls: list[tuple[Operation, tuple[str, str] | None]] = []
        self.failures: dict[tuple[Operation, tuple[str, str] | None], RunnerFailure] = {}

    def run_text(self, operation: Operation) -> str:
        self.calls.append((operation, None))
        failure = self.failures.get((operation, None))
        if failure:
            raise failure
        return self.context

    def run_json(self, operation: Operation, target=None):  # type: ignore[no-untyped-def]
        self.calls.append((operation, target))
        failure = self.failures.get((operation, target))
        if failure:
            raise failure
        if operation is Operation.VERSION:
            return deepcopy(self.fixture["version"])
        if operation is Operation.NODES:
            return deepcopy(self.fixture["nodes"])
        if operation is Operation.DEPLOYMENT:
            return deepcopy(self.fixture["deployments"]["/".join(target)])
        if operation is Operation.PODS:
            return deepcopy(self.fixture["pods"]["/".join(target)])
        if operation is Operation.ENDPOINT_SLICES:
            return deepcopy(self.fixture["routing"]["/".join(target)])
        if operation is Operation.METRICS_API_SERVICE:
            return deepcopy(self.fixture["metrics"])
        raise AssertionError(f"unexpected operation: {operation}")


class FakeHttp:
    def __init__(self, fixture: dict) -> None:
        self.fixture = fixture

    def get(self, base_url: str, path: str) -> HttpResponse:
        application = "restaurant-api" if "30080" in base_url else "forge-yaml-workbench"
        value = self.fixture[f"{application}{path}"]
        body = value.encode() if isinstance(value, str) else json.dumps(value).encode()
        return HttpResponse(200, body)


class ForgeOpsSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads((FIXTURES / "healthy.json").read_text(encoding="utf-8"))
        self.http_fixture = json.loads((FIXTURES / "http.json").read_text(encoding="utf-8"))

    def collect(self, fixture=None, include_http: bool = False):  # type: ignore[no-untyped-def]
        runner = FakeKubectl(fixture or self.fixture)
        collector = Collector(runner, FakeHttp(self.http_fixture))
        raw = collector.collect(
            "http://192.0.2.10:30080" if include_http else None,
            "http://192.0.2.10:30081" if include_http else None,
        )
        return runner, raw, evaluate(raw)

    def test_healthy_fixture_passes_with_stable_order(self) -> None:
        _, raw, snapshot = self.collect(include_http=True)
        self.assertEqual(0, snapshot.exit_code)
        self.assertTrue(all(check.status is Status.PASS for check in snapshot.checks))
        ids = [check.check_id for check in snapshot.checks]
        self.assertEqual("context", ids[0])
        self.assertEqual("kubernetes.version", ids[1])
        self.assertEqual("node.forge-head", ids[2])
        self.assertLess(ids.index("pod.forge-restaurant.restaurant-api-a"), ids.index("pod.forge-restaurant.restaurant-api-b"))
        self.assertEqual("http.restaurant-api/version", ids[-5])
        self.assertNotIn("addresses", repr(raw.evidence))

    def test_absent_optional_urls_do_not_create_false_passes(self) -> None:
        _, _, snapshot = self.collect()
        self.assertEqual(0, snapshot.exit_code)
        self.assertFalse(any(check.check_id.startswith("http.") for check in snapshot.checks))

    def test_not_ready_node_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["nodes"]["items"][0]["status"]["conditions"][0]["status"] = "False"
        _, _, snapshot = self.collect(fixture)
        node = next(check for check in snapshot.checks if check.check_id == "node.forge-node-03")
        self.assertEqual(Status.FAIL, node.status)
        self.assertEqual(1, snapshot.exit_code)

    def test_duplicate_node_identity_is_unknown(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["nodes"]["items"].append(deepcopy(fixture["nodes"]["items"][1]))
        _, _, snapshot = self.collect(fixture)
        head = next(check for check in snapshot.checks if check.check_id == "node.forge-head")
        self.assertEqual(Status.UNKNOWN, head.status)
        self.assertEqual(2, snapshot.exit_code)

    def test_missing_node_is_unknown(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["nodes"]["items"] = [
            node for node in fixture["nodes"]["items"]
            if node["metadata"]["name"] != "forge-node-02"
        ]
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "node.forge-node-02")
        self.assertEqual(Status.UNKNOWN, check.status)

    def test_deployment_shortfall_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["deployments"]["forge-restaurant/restaurant-api"]["status"]["readyReplicas"] = 2
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "deployment.forge-restaurant.restaurant-api")
        self.assertEqual(Status.FAIL, check.status)

    def test_configured_deployment_image_mismatch_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        containers = fixture["deployments"]["forge-restaurant/restaurant-api"]["spec"]["template"]["spec"]["containers"]
        containers[0]["image"] = "wmstipes/signalforge-restaurant-api:latest"
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "deployment.forge-restaurant.restaurant-api")
        self.assertEqual(Status.FAIL, check.status)

    def test_missing_selected_pod_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["pods"]["forge-restaurant/restaurant-api"]["items"].pop()
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "pods.forge-restaurant.restaurant-api")
        self.assertEqual(Status.FAIL, check.status)

    def test_restarted_pod_warns_and_pending_pod_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        pods = fixture["pods"]["forge-restaurant/restaurant-api"]["items"]
        pods[0]["status"]["containerStatuses"][0]["restartCount"] = 2
        pods[1]["status"]["phase"] = "Pending"
        _, _, snapshot = self.collect(fixture)
        self.assertEqual(Status.WARN, next(check for check in snapshot.checks if check.check_id.endswith("restaurant-api-c")).status)
        self.assertEqual(Status.FAIL, next(check for check in snapshot.checks if check.check_id.endswith("restaurant-api-a")).status)

    def test_pinned_runtime_digest_mismatch_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        pod = fixture["pods"]["forge-tools/forge-yaml-workbench"]["items"][0]
        pod["status"]["containerStatuses"][0]["imageID"] = "docker.io/example@sha256:different"
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id.endswith("workbench-a"))
        self.assertEqual(Status.FAIL, check.status)

    def test_partial_endpoint_slice_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        endpoints = fixture["routing"]["forge-restaurant/restaurant-api"]["items"][0]["endpoints"]
        endpoints[0]["conditions"]["ready"] = False
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "routing.forge-restaurant.restaurant-api")
        self.assertEqual(Status.FAIL, check.status)

    def test_empty_and_unknown_endpoint_slices_fail(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["routing"]["forge-observability/prometheus"]["items"] = []
        endpoints = fixture["routing"]["forge-observability/grafana"]["items"][0]["endpoints"]
        endpoints[0]["conditions"]["ready"] = None
        _, _, snapshot = self.collect(fixture)
        prometheus = next(check for check in snapshot.checks if check.check_id == "routing.forge-observability.prometheus")
        grafana = next(check for check in snapshot.checks if check.check_id == "routing.forge-observability.grafana")
        self.assertEqual(Status.FAIL, prometheus.status)
        self.assertEqual(Status.FAIL, grafana.status)

    def test_unavailable_metrics_api_fails(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["metrics"]["status"]["conditions"][0]["status"] = "False"
        _, _, snapshot = self.collect(fixture)
        check = next(check for check in snapshot.checks if check.check_id == "metrics-api-service")
        self.assertEqual(Status.FAIL, check.status)

    def test_http_mismatch_fails(self) -> None:
        self.http_fixture["restaurant-api/version"]["version"] = "0.6.0"
        _, _, snapshot = self.collect(include_http=True)
        check = next(check for check in snapshot.checks if check.check_id == "http.restaurant-api/version")
        self.assertEqual(Status.FAIL, check.status)

    def test_collection_failure_is_unknown_and_takes_exit_precedence(self) -> None:
        runner = FakeKubectl(self.fixture)
        runner.failures[(Operation.NODES, None)] = RunnerFailure("timeout", "timed out")
        raw = Collector(runner, FakeHttp(self.http_fixture)).collect()
        snapshot = evaluate(raw)
        self.assertEqual(2, snapshot.exit_code)
        self.assertEqual(4, sum(check.status is Status.UNKNOWN for check in snapshot.checks))

    def test_total_collection_budget_fails_remaining_checks_closed(self) -> None:
        ticks = iter((0.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0,
                      100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0,
                      100.0, 100.0, 100.0, 100.0))
        runner = FakeKubectl(self.fixture)
        raw = Collector(runner, clock=lambda: next(ticks)).collect()
        snapshot = evaluate(raw)
        self.assertEqual(2, snapshot.exit_code)
        self.assertTrue(any(item.error and item.error.category == "collection-timeout" for item in raw.evidence))

    def test_unexpected_kubernetes_shape_becomes_unknown(self) -> None:
        fixture = deepcopy(self.fixture)
        fixture["nodes"] = {"unexpected": []}
        _, raw, snapshot = self.collect(fixture)
        evidence = next(item for item in raw.evidence if item.evidence_id == "nodes")
        self.assertEqual("unexpected-shape", evidence.error.category)
        self.assertEqual(2, snapshot.exit_code)

    def test_context_mismatch_stops_before_resource_queries(self) -> None:
        runner = FakeKubectl(self.fixture, context="wrong-context")
        runner.context = EXPECTED_CONTEXT
        runner.run_text = lambda operation: "wrong-context"  # type: ignore[method-assign]
        raw = Collector(runner).collect()
        snapshot = evaluate(raw)
        self.assertEqual(2, snapshot.exit_code)
        self.assertEqual(["context"], [check.check_id for check in snapshot.checks])
        self.assertEqual(1, len(raw.evidence))

    def test_renderers_preserve_check_semantics_and_redaction(self) -> None:
        _, _, snapshot = self.collect(include_http=True)
        terminal = StringIO()
        markdown = StringIO()
        json_output = StringIO()
        render_text(snapshot, terminal)
        render_markdown(snapshot, markdown)
        render_json(snapshot, json_output)
        payload = json.loads(json_output.getvalue())
        for check in snapshot.checks:
            self.assertIn(check.check_id, terminal.getvalue())
            self.assertIn(check.check_id, markdown.getvalue())
        self.assertEqual(
            [check.check_id for check in snapshot.checks],
            [check["id"] for check in payload["checks"]],
        )
        self.assertEqual(
            [check.status.value for check in snapshot.checks],
            [check["status"] for check in payload["checks"]],
        )
        self.assertEqual(snapshot.exit_code, payload["summary"]["exitCode"])
        self.assertEqual(snapshot.overall_status.value, payload["summary"]["overallStatus"])
        combined = terminal.getvalue() + markdown.getvalue() + json_output.getvalue()
        self.assertNotIn("192.0.2.10", combined)
        self.assertNotIn("/explicit/config", combined)
        self.assertIn("not continuous monitoring", markdown.getvalue())

    def test_json_renderer_matches_golden_contract(self) -> None:
        snapshot = EvaluatedSnapshot(
            schema="forgeops.snapshot/v1alpha1",
            collected_at_utc="2026-09-16T18:00:00Z",
            context=EXPECTED_CONTEXT,
            checks=(
                CheckResult(
                    "node.forge-head", Status.PASS, "Node is Ready",
                    "kubectl get nodes -o json", "2026-09-16T18:00:00Z",
                    "Ready=True", "Ready=True",
                ),
                CheckResult(
                    "metrics-api-service", Status.UNKNOWN,
                    "Metrics APIService evidence is incomplete",
                    "APIService v1beta1.metrics.k8s.io", "2026-09-16T18:00:00Z",
                    error_category="timeout",
                ),
            ),
        )
        first = StringIO()
        second = StringIO()
        render_json(snapshot, first)
        render_json(snapshot, second)
        expected = (FIXTURES / "evaluated-json-golden.json").read_text(encoding="utf-8")
        self.assertEqual(expected, first.getvalue())
        self.assertEqual(first.getvalue(), second.getvalue())
        payload = json.loads(first.getvalue())
        self.assertNotIn("expected", payload["checks"][1])
        self.assertNotIn("observed", payload["checks"][1])

    def test_json_summary_preserves_warn_fail_and_unknown_precedence(self) -> None:
        fixture = deepcopy(self.fixture)
        pods = fixture["pods"]["forge-restaurant/restaurant-api"]["items"]
        pods[0]["status"]["containerStatuses"][0]["restartCount"] = 1
        pods[1]["status"]["phase"] = "Pending"
        fixture["nodes"]["items"] = [
            node for node in fixture["nodes"]["items"]
            if node["metadata"]["name"] != "forge-node-02"
        ]
        _, _, snapshot = self.collect(fixture)
        output = StringIO()
        render_json(snapshot, output)
        payload = json.loads(output.getvalue())
        self.assertGreater(payload["summary"]["warn"], 0)
        self.assertGreater(payload["summary"]["fail"], 0)
        self.assertGreater(payload["summary"]["unknown"], 0)
        self.assertEqual("UNKNOWN", payload["summary"]["overallStatus"])
        self.assertEqual(2, payload["summary"]["exitCode"])


if __name__ == "__main__":
    unittest.main()
