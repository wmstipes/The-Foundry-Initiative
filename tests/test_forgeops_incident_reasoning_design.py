from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.comparison import load_comparison_file  # noqa: E402
from forgeops.runbook_mapping import map_runbooks  # noqa: E402
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"
EVALUATION = ROOT / "tests" / "fixtures" / "forgeops" / "incident-reasoning-evaluation.json"
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"

TOP_FIELDS = ("schema", "cases", "limitations")
CASE_FIELDS = (
    "id", "scenario", "expectedState", "expectedComparisonExit",
    "expectedMappingExit", "expectedDeltaIds", "expectedRunbookIds",
    "requiredUncertainties", "forbiddenClaims",
)
STATES = {"STABLE", "DEGRADED", "INCOMPLETE", "RECOVERED"}
FORBIDDEN = [
    "causation", "current-health", "operational-severity", "remediation-authority",
]
LIMITATION = (
    "This synthetic corpus defines evaluation expectations for a future bounded "
    "incident brief; it is not captured cluster evidence, a diagnosis, a "
    "recommendation, training data, or remediation authority."
)


class ForgeOpsIncidentReasoningDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = EVALUATION.read_bytes()
        self.document = json.loads(self.raw)

    def test_evaluation_contract_is_exact_and_bounded(self) -> None:
        self.assertLessEqual(len(self.raw), 64 * 1024)
        self.assertEqual(TOP_FIELDS, tuple(self.document))
        self.assertEqual("forgeops.incident-evaluation/v1alpha1", self.document["schema"])
        self.assertEqual([LIMITATION], self.document["limitations"])
        cases = self.document["cases"]
        self.assertEqual(sorted(case["id"] for case in cases), [case["id"] for case in cases])
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        self.assertEqual(5, len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(CASE_FIELDS, tuple(case))
                self.assertEqual(case["id"], case["scenario"])
                self.assertIn(case["expectedState"], STATES)
                self.assertIn(case["expectedComparisonExit"], (0, 1))
                self.assertIn(case["expectedMappingExit"], (0, 1))
                self.assertEqual(sorted(set(case["expectedDeltaIds"])), case["expectedDeltaIds"])
                self.assertEqual(sorted(set(case["expectedRunbookIds"])), case["expectedRunbookIds"])
                self.assertEqual(sorted(set(case["requiredUncertainties"])), case["requiredUncertainties"])
                self.assertEqual(FORBIDDEN, case["forbiddenClaims"])

    def test_cases_cover_the_exact_synthetic_scenario_inventory(self) -> None:
        scenario_names = sorted(path.name for path in SCENARIO_ROOT.iterdir() if path.is_dir())
        self.assertEqual(scenario_names, [case["scenario"] for case in self.document["cases"]])

    def test_expectations_are_grounded_in_current_comparison_and_mapping(self) -> None:
        catalog = load_runbook_catalog(str(CATALOG))
        for case in self.document["cases"]:
            scenario = SCENARIO_ROOT / case["scenario"]
            comparison = load_comparison_file(str(scenario / "expected-comparison.json"))
            mapping = map_runbooks(comparison, catalog)
            with self.subTest(case=case["id"]):
                self.assertEqual(case["expectedComparisonExit"], comparison.exit_code)
                self.assertEqual(case["expectedMappingExit"], mapping.exit_code)
                self.assertEqual(
                    case["expectedDeltaIds"],
                    [delta.check_id for delta in comparison.deltas],
                )
                self.assertEqual(
                    case["expectedRunbookIds"],
                    [match.runbook_id for match in mapping.matches],
                )

    def test_corpus_contains_no_live_signalforge_identifiers_or_addresses(self) -> None:
        text = self.raw.decode("utf-8")
        for forbidden in (
            "forge-head", "forge-node-01", "192.168.", "kubernetes-admin@kubernetes",
            "kubeconfig", "credential", "secret",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_runtime_brief_has_no_model_dependency(self) -> None:
        from forgeops.cli import build_parser

        args = build_parser().parse_args([
            "incident", "brief", "--comparison", "comparison.json",
            "--mapping", "mapping.json", "--format", "json",
        ])
        self.assertEqual("incident", args.command)
        self.assertEqual("brief", args.incident_command)
        self.assertEqual([], [name for name in sys.modules if name.startswith("openai")])


if __name__ == "__main__":
    unittest.main()
