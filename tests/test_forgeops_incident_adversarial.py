from __future__ import annotations

import json
from pathlib import Path
import sys
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import build_parser  # noqa: E402
from forgeops.comparison import (  # noqa: E402
    CheckDelta,
    DeltaKind,
    EvidenceComparison,
    load_comparison_file,
)
from forgeops.incident import IncidentBriefError, build_incident_brief  # noqa: E402
from forgeops.models import Status  # noqa: E402
from forgeops.runbook_mapping import (  # noqa: E402
    MappingReason,
    RunbookMapping,
    RunbookMatch,
    map_runbooks,
)
from forgeops.runbooks import load_runbook_catalog  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "tests" / "fixtures" / "forgeops" / "incident-adversarial-evaluation.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "forgeops" / "scenarios"
CATALOG = ROOT / "docs" / "reference" / "forgeops-runbook-catalog.json"

TOP_FIELDS = ("schema", "cases", "decision", "limitations")
CASE_FIELDS = (
    "id", "expectedDisposition", "expectedCode", "expectedState",
    "requiredUncertainties", "protectedBoundary",
)
LIMITATION = (
    "These synthetic adversarial cases evaluate deterministic trust boundaries; "
    "they are not captured incidents, model training data, current-health claims, "
    "or remediation authority."
)


class ForgeOpsIncidentAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = EVALUATION.read_bytes()
        self.document = json.loads(self.raw)
        self.catalog = load_runbook_catalog(str(CATALOG))

    @staticmethod
    def comparison(*deltas: CheckDelta) -> EvidenceComparison:
        return EvidenceComparison(
            "forgeops.snapshot/v1alpha1",
            "2026-09-19T00:00:00Z",
            "2026-09-19T00:01:00Z",
            Status.PASS,
            Status.PASS,
            len(deltas),
            0,
            deltas,
        )

    @staticmethod
    def unmapped(comparison: EvidenceComparison) -> RunbookMapping:
        return RunbookMapping(
            comparison.before_collected_at_utc,
            comparison.after_collected_at_utc,
            len(comparison.deltas),
            (),
            tuple(delta.check_id for delta in comparison.deltas),
        )

    def execute(self, case_id: str) -> tuple[str, str | None, str | None, list[str]]:
        if case_id in {"stale-mapping-window", "fabricated-reason-status", "structurally-valid-altered-title", "mapping-coverage-gap"}:
            comparison = load_comparison_file(
                str(SCENARIOS / "routing-regression" / "expected-comparison.json"),
            )
            mapping = map_runbooks(comparison, self.catalog)
            if case_id == "stale-mapping-window":
                mapping = RunbookMapping(
                    "2026-09-01T00:00:00Z", mapping.after_collected_at_utc,
                    mapping.total_deltas, mapping.matches, mapping.unmapped_delta_ids,
                )
            elif case_id == "fabricated-reason-status":
                match = mapping.matches[0]
                reason = match.reasons[0]
                changed = RunbookMatch(
                    match.runbook_id, match.title, match.path, match.section,
                    (MappingReason(reason.check_id, reason.delta_kind, Status.WARN),),
                )
                mapping = RunbookMapping(
                    mapping.before_collected_at_utc, mapping.after_collected_at_utc,
                    mapping.total_deltas, (changed,), mapping.unmapped_delta_ids,
                )
            elif case_id == "structurally-valid-altered-title":
                match = mapping.matches[0]
                changed = RunbookMatch(
                    match.runbook_id, "Altered but structurally valid title",
                    match.path, match.section, match.reasons,
                )
                mapping = RunbookMapping(
                    mapping.before_collected_at_utc, mapping.after_collected_at_utc,
                    mapping.total_deltas, (changed,), mapping.unmapped_delta_ids,
                )
            else:
                mapping = self.unmapped(comparison)
        elif case_id == "neutral-evidence-change":
            comparison = self.comparison(CheckDelta(
                "synthetic.neutral", DeltaKind.EVIDENCE_CHANGED,
                Status.PASS, Status.PASS, ("observation",),
            ))
            mapping = self.unmapped(comparison)
        elif case_id == "added-passing-check":
            comparison = self.comparison(CheckDelta(
                "synthetic.added", DeltaKind.ADDED, None, Status.PASS,
            ))
            mapping = self.unmapped(comparison)
        elif case_id == "removed-check":
            comparison = self.comparison(CheckDelta(
                "synthetic.removed", DeltaKind.REMOVED, Status.PASS, None,
            ))
            mapping = self.unmapped(comparison)
        elif case_id == "mixed-unknown-and-failure":
            comparison = self.comparison(
                CheckDelta("synthetic.fail", DeltaKind.STATUS_CHANGED, Status.PASS, Status.FAIL, ("status",)),
                CheckDelta("synthetic.unknown", DeltaKind.STATUS_CHANGED, Status.PASS, Status.UNKNOWN, ("status",)),
            )
            mapping = self.unmapped(comparison)
        elif case_id == "mixed-recovery-neutral-change":
            comparison = self.comparison(
                CheckDelta("synthetic.neutral", DeltaKind.EVIDENCE_CHANGED, Status.PASS, Status.PASS, ("observation",)),
                CheckDelta("synthetic.recovered", DeltaKind.STATUS_CHANGED, Status.FAIL, Status.PASS, ("status",)),
            )
            mapping = self.unmapped(comparison)
        else:  # pragma: no cover - exact corpus inventory protects this branch.
            raise AssertionError(f"unhandled adversarial case: {case_id}")

        try:
            brief = build_incident_brief(comparison, mapping)
        except IncidentBriefError as exc:
            return "REJECT", exc.code, None, []
        disposition = (
            "ACCEPT_UNAUTHENTICATED"
            if case_id == "structurally-valid-altered-title"
            else "ACCEPT"
        )
        return disposition, None, brief.state.value, list(brief.uncertainties)

    def test_evaluation_contract_is_exact_bounded_and_sorted(self) -> None:
        self.assertLessEqual(len(self.raw), 64 * 1024)
        self.assertEqual(TOP_FIELDS, tuple(self.document))
        self.assertEqual(
            "forgeops.incident-adversarial-evaluation/v1alpha1",
            self.document["schema"],
        )
        cases = self.document["cases"]
        self.assertEqual(9, len(cases))
        self.assertEqual(sorted(case["id"] for case in cases), [case["id"] for case in cases])
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            self.assertEqual(CASE_FIELDS, tuple(case))
            self.assertEqual(
                sorted(set(case["requiredUncertainties"])),
                case["requiredUncertainties"],
            )
        self.assertEqual("DEFER_MODEL_AND_RETRIEVAL", self.document["decision"])
        self.assertEqual([LIMITATION], self.document["limitations"])

    def test_every_adversarial_expectation_matches_production_behavior(self) -> None:
        for case in self.document["cases"]:
            actual = self.execute(case["id"])
            expected = (
                case["expectedDisposition"],
                case["expectedCode"],
                case["expectedState"],
                case["requiredUncertainties"],
            )
            with self.subTest(case=case["id"]):
                self.assertEqual(expected, actual)

    def test_decision_adds_no_runtime_or_dependency_authority(self) -> None:
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual("0.15.0", package["project"]["version"])
        self.assertEqual([], package["project"]["dependencies"])
        self.assertEqual([], [name for name in sys.modules if name.startswith("openai")])
        parser = build_parser()
        help_text = parser.format_help()
        self.assertNotIn("model", help_text)
        self.assertNotIn("retrieval", help_text)


if __name__ == "__main__":
    unittest.main()
