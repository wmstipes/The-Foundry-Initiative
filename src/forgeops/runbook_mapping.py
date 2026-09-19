"""Deterministic offline mapping from comparison deltas to runbook knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import TextIO

from .comparison import CheckDelta, EvidenceComparison
from .models import Status
from .runbooks import RunbookCatalog, RunbookEntry, RunbookSignal


RUNBOOK_MAPPING_SCHEMA = "forgeops.runbook-mapping/v1alpha1"
RUNBOOK_MAPPING_LIMITATION = (
    "This deterministic mapping reports catalog rules matched by comparison "
    "deltas; it does not establish causation, operational severity, diagnosis, "
    "recommendation, or remediation authority."
)


@dataclass(frozen=True, slots=True)
class MappingReason:
    check_id: str
    delta_kind: str
    after_status: Status


@dataclass(frozen=True, slots=True)
class RunbookMatch:
    runbook_id: str
    title: str
    path: str
    section: str
    reasons: tuple[MappingReason, ...]


@dataclass(frozen=True, slots=True)
class RunbookMapping:
    before_collected_at_utc: str
    after_collected_at_utc: str
    total_deltas: int
    matches: tuple[RunbookMatch, ...]
    unmapped_delta_ids: tuple[str, ...]

    @property
    def mapped_delta_ids(self) -> tuple[str, ...]:
        return tuple(sorted({reason.check_id for match in self.matches for reason in match.reasons}))

    @property
    def exit_code(self) -> int:
        return 1 if self.unmapped_delta_ids else 0


def _selector_matches(signal: RunbookSignal, delta: CheckDelta) -> bool:
    identifier_matches = (
        delta.check_id == signal.check_id
        if signal.match == "exact"
        else delta.check_id.startswith(signal.check_id)
    )
    return (
        identifier_matches
        and delta.kind in signal.delta_kinds
        and delta.after_status is not None
        and delta.after_status in signal.after_statuses
    )


def _entry_reasons(entry: RunbookEntry, deltas: tuple[CheckDelta, ...]) -> tuple[MappingReason, ...]:
    reasons: list[MappingReason] = []
    for delta in deltas:
        if any(_selector_matches(signal, delta) for signal in entry.signals):
            assert delta.after_status is not None
            reasons.append(MappingReason(
                check_id=delta.check_id,
                delta_kind=delta.kind.value,
                after_status=delta.after_status,
            ))
    return tuple(reasons)


def map_runbooks(
    comparison: EvidenceComparison,
    catalog: RunbookCatalog,
) -> RunbookMapping:
    """Apply catalog selectors to immutable comparison deltas."""

    matches: list[RunbookMatch] = []
    mapped: set[str] = set()
    for entry in catalog.entries:
        reasons = _entry_reasons(entry, comparison.deltas)
        if not reasons:
            continue
        mapped.update(reason.check_id for reason in reasons)
        matches.append(RunbookMatch(
            entry.runbook_id, entry.title, entry.path, entry.section, reasons,
        ))
    unmapped = tuple(
        delta.check_id for delta in comparison.deltas if delta.check_id not in mapped
    )
    return RunbookMapping(
        before_collected_at_utc=comparison.before_collected_at_utc,
        after_collected_at_utc=comparison.after_collected_at_utc,
        total_deltas=len(comparison.deltas),
        matches=tuple(matches),
        unmapped_delta_ids=unmapped,
    )


def render_runbook_mapping_text(mapping: RunbookMapping, stream: TextIO) -> None:
    """Render a bounded, deterministic human-readable mapping."""

    status = "COMPLETE" if mapping.exit_code == 0 else "INCOMPLETE"
    stream.write(
        f"{status} {RUNBOOK_MAPPING_SCHEMA} totalDeltas={mapping.total_deltas} "
        f"mappedDeltas={len(mapping.mapped_delta_ids)} "
        f"unmappedDeltas={len(mapping.unmapped_delta_ids)} "
        f"runbookMatches={len(mapping.matches)} mappingExit={mapping.exit_code}\n"
    )
    for match in mapping.matches:
        stream.write(
            f"RUNBOOK {match.runbook_id} {match.path}#{match.section}\n"
        )
        for reason in match.reasons:
            stream.write(
                f"  MATCH {reason.check_id} {reason.delta_kind} "
                f"after={reason.after_status.value}\n"
            )
    for check_id in mapping.unmapped_delta_ids:
        stream.write(f"UNMAPPED {check_id}\n")
    stream.write(f"LIMITATION {RUNBOOK_MAPPING_LIMITATION}\n")


def render_runbook_mapping_json(mapping: RunbookMapping, stream: TextIO) -> None:
    """Render the disclosure-bounded mapping contract."""

    payload = {
        "schema": RUNBOOK_MAPPING_SCHEMA,
        "comparisonSchema": "forgeops.comparison/v1alpha1",
        "beforeCollectedAtUtc": mapping.before_collected_at_utc,
        "afterCollectedAtUtc": mapping.after_collected_at_utc,
        "summary": {
            "totalDeltas": mapping.total_deltas,
            "mappedDeltas": len(mapping.mapped_delta_ids),
            "unmappedDeltas": len(mapping.unmapped_delta_ids),
            "runbookMatches": len(mapping.matches),
            "mappingExit": mapping.exit_code,
        },
        "matches": [
            {
                "runbookId": match.runbook_id,
                "title": match.title,
                "path": match.path,
                "section": match.section,
                "reasons": [
                    {
                        "checkId": reason.check_id,
                        "deltaKind": reason.delta_kind,
                        "afterStatus": reason.after_status.value,
                    }
                    for reason in match.reasons
                ],
            }
            for match in mapping.matches
        ],
        "unmappedDeltaIds": list(mapping.unmapped_delta_ids),
        "limitations": [RUNBOOK_MAPPING_LIMITATION],
    }
    json.dump(payload, stream, ensure_ascii=True, indent=2)
    stream.write("\n")
