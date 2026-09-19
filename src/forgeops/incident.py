"""Deterministic, artifact-bounded ForgeOps incident briefs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from typing import TextIO

from .comparison import DeltaKind, EvidenceComparison
from .models import Status
from .runbook_mapping import RunbookMapping, RunbookMatch


INCIDENT_BRIEF_SCHEMA = "forgeops.incident-brief/v1alpha1"
INCIDENT_LIMITATIONS = (
    "This brief summarizes only supplied validated artifacts; it does not establish current health, causation, operational severity, diagnosis, impact, or remediation authority.",
    "Runbook references are catalog-rule matches for operator review; they do not prove that a procedure applies or authorize its execution.",
)


class IncidentState(StrEnum):
    STABLE = "STABLE"
    CHANGED = "CHANGED"
    DEGRADED = "DEGRADED"
    INCOMPLETE = "INCOMPLETE"
    RECOVERED = "RECOVERED"


class IncidentBriefError(ValueError):
    """A bounded, non-sensitive incident-brief construction failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


@dataclass(frozen=True, slots=True)
class IncidentFact:
    check_id: str
    delta_kind: DeltaKind
    before_status: Status | None
    after_status: Status | None


@dataclass(frozen=True, slots=True)
class IncidentBrief:
    before_collected_at_utc: str
    after_collected_at_utc: str
    state: IncidentState
    facts: tuple[IncidentFact, ...]
    runbooks: tuple[RunbookMatch, ...]
    unmapped_delta_ids: tuple[str, ...]
    uncertainties: tuple[str, ...]


def classify_incident_state(comparison: EvidenceComparison) -> IncidentState:
    """Classify only the supplied comparison window with a total rule set."""

    if not comparison.deltas:
        return IncidentState.STABLE
    if any(
        delta.after_status is None or delta.after_status is Status.UNKNOWN
        for delta in comparison.deltas
    ):
        return IncidentState.INCOMPLETE
    if any(
        delta.after_status in (Status.WARN, Status.FAIL)
        for delta in comparison.deltas
    ):
        return IncidentState.DEGRADED
    if all(
        delta.kind is DeltaKind.STATUS_CHANGED
        and delta.before_status is not None
        and delta.before_status is not Status.PASS
        and delta.after_status is Status.PASS
        for delta in comparison.deltas
    ):
        return IncidentState.RECOVERED
    return IncidentState.CHANGED


def _validate_mapping_linkage(
    comparison: EvidenceComparison,
    mapping: RunbookMapping,
) -> None:
    if (
        mapping.before_collected_at_utc != comparison.before_collected_at_utc
        or mapping.after_collected_at_utc != comparison.after_collected_at_utc
    ):
        raise IncidentBriefError(
            "window-mismatch", "comparison and mapping windows do not match",
        )
    if mapping.total_deltas != len(comparison.deltas):
        raise IncidentBriefError(
            "delta-count-mismatch", "comparison and mapping delta counts do not match",
        )
    deltas = {delta.check_id: delta for delta in comparison.deltas}
    mapped_ids: set[str] = set()
    for match in mapping.matches:
        for reason in match.reasons:
            delta = deltas.get(reason.check_id)
            if (
                delta is None
                or delta.kind.value != reason.delta_kind
                or delta.after_status is not reason.after_status
            ):
                raise IncidentBriefError(
                    "mapping-mismatch",
                    "mapping reasons do not match the supplied comparison",
                )
            mapped_ids.add(reason.check_id)
    comparison_ids = set(deltas)
    if set(mapping.unmapped_delta_ids) != comparison_ids - mapped_ids:
        raise IncidentBriefError(
            "mapping-coverage-mismatch",
            "mapping coverage does not match the supplied comparison",
        )


def build_incident_brief(
    comparison: EvidenceComparison,
    mapping: RunbookMapping,
) -> IncidentBrief:
    """Build a deterministic brief from two already validated artifacts."""

    _validate_mapping_linkage(comparison, mapping)
    state = classify_incident_state(comparison)
    uncertainties = {"point-in-time-only"}
    if comparison.deltas:
        uncertainties.add("cause-not-established")
    if state is IncidentState.INCOMPLETE:
        uncertainties.add("evidence-incomplete")
    if mapping.unmapped_delta_ids:
        uncertainties.add("mapping-incomplete")
    return IncidentBrief(
        comparison.before_collected_at_utc,
        comparison.after_collected_at_utc,
        state,
        tuple(
            IncidentFact(
                delta.check_id,
                delta.kind,
                delta.before_status,
                delta.after_status,
            )
            for delta in comparison.deltas
        ),
        mapping.matches,
        mapping.unmapped_delta_ids,
        tuple(sorted(uncertainties)),
    )


def render_incident_brief_json(brief: IncidentBrief, stream: TextIO) -> None:
    """Render the deterministic disclosure-bounded brief contract."""

    payload = {
        "schema": INCIDENT_BRIEF_SCHEMA,
        "comparisonSchema": "forgeops.comparison/v1alpha1",
        "mappingSchema": "forgeops.runbook-mapping/v1alpha1",
        "beforeCollectedAtUtc": brief.before_collected_at_utc,
        "afterCollectedAtUtc": brief.after_collected_at_utc,
        "state": brief.state.value,
        "facts": [
            {
                "id": fact.check_id,
                "kind": fact.delta_kind.value,
                "beforeStatus": (
                    fact.before_status.value if fact.before_status is not None else None
                ),
                "afterStatus": (
                    fact.after_status.value if fact.after_status is not None else None
                ),
            }
            for fact in brief.facts
        ],
        "runbooks": [
            {
                "runbookId": runbook.runbook_id,
                "title": runbook.title,
                "path": runbook.path,
                "section": runbook.section,
                "reasons": [
                    {
                        "checkId": reason.check_id,
                        "deltaKind": reason.delta_kind,
                        "afterStatus": reason.after_status.value,
                    }
                    for reason in runbook.reasons
                ],
            }
            for runbook in brief.runbooks
        ],
        "unmappedDeltaIds": list(brief.unmapped_delta_ids),
        "uncertainties": list(brief.uncertainties),
        "limitations": list(INCIDENT_LIMITATIONS),
    }
    json.dump(payload, stream, ensure_ascii=True, indent=2)
    stream.write("\n")
