"""Deterministic comparison of contract-validated ForgeOps evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TextIO

from .evidence import ValidatedEvidence
from .models import CheckResult, Status


class EvidenceComparisonError(ValueError):
    """A bounded, non-sensitive evidence comparison failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


class DeltaKind(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    STATUS_CHANGED = "STATUS_CHANGED"
    EVIDENCE_CHANGED = "EVIDENCE_CHANGED"


@dataclass(frozen=True, slots=True)
class CheckDelta:
    check_id: str
    kind: DeltaKind
    before_status: Status | None
    after_status: Status | None
    changed_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceComparison:
    schema: str
    before_collected_at_utc: str
    after_collected_at_utc: str
    before_overall_status: Status
    after_overall_status: Status
    total_checks: int
    unchanged_checks: int
    deltas: tuple[CheckDelta, ...]

    @property
    def exit_code(self) -> int:
        return 1 if self.deltas else 0


_COMPARED_FIELDS = (
    ("status", "status"),
    ("observation", "observation"),
    ("source", "source"),
    ("expected", "expected"),
    ("observed", "observed"),
    ("errorCategory", "error_category"),
)


def _timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def _changed_fields(before: CheckResult, after: CheckResult) -> tuple[str, ...]:
    return tuple(
        output_name
        for output_name, attribute in _COMPARED_FIELDS
        if getattr(before, attribute) != getattr(after, attribute)
    )


def compare_evidence(
    before: ValidatedEvidence,
    after: ValidatedEvidence,
) -> EvidenceComparison:
    """Compare two validated artifacts without collecting or inferring evidence."""

    before_snapshot = before.snapshot
    after_snapshot = after.snapshot
    if (
        _timestamp(after_snapshot.collected_at_utc)
        < _timestamp(before_snapshot.collected_at_utc)
    ):
        raise EvidenceComparisonError(
            "reversed-chronology",
            "after evidence must not predate before evidence",
        )

    before_checks = {check.check_id: check for check in before_snapshot.checks}
    after_checks = {check.check_id: check for check in after_snapshot.checks}
    deltas: list[CheckDelta] = []
    unchanged = 0
    all_check_ids = before_checks.keys() | after_checks.keys()
    for check_id in sorted(all_check_ids):
        before_check = before_checks.get(check_id)
        after_check = after_checks.get(check_id)
        if before_check is None and after_check is not None:
            deltas.append(CheckDelta(
                check_id, DeltaKind.ADDED, None, after_check.status,
            ))
            continue
        if after_check is None and before_check is not None:
            deltas.append(CheckDelta(
                check_id, DeltaKind.REMOVED, before_check.status, None,
            ))
            continue
        if before_check is None or after_check is None:  # Defensive narrowing.
            raise AssertionError("comparison identity invariant failed")
        fields = _changed_fields(before_check, after_check)
        if not fields:
            unchanged += 1
            continue
        kind = (
            DeltaKind.STATUS_CHANGED
            if before_check.status != after_check.status
            else DeltaKind.EVIDENCE_CHANGED
        )
        deltas.append(CheckDelta(
            check_id,
            kind,
            before_check.status,
            after_check.status,
            fields,
        ))

    return EvidenceComparison(
        schema=before_snapshot.schema,
        before_collected_at_utc=before_snapshot.collected_at_utc,
        after_collected_at_utc=after_snapshot.collected_at_utc,
        before_overall_status=before_snapshot.overall_status,
        after_overall_status=after_snapshot.overall_status,
        total_checks=len(all_check_ids),
        unchanged_checks=unchanged,
        deltas=tuple(deltas),
    )


def render_comparison_text(comparison: EvidenceComparison, stream: TextIO) -> None:
    """Render one deterministic, human-reviewable comparison."""

    stream.write("ForgeOps evidence comparison\n")
    stream.write(f"Schema: {comparison.schema}\n")
    stream.write(f"Before: {comparison.before_collected_at_utc}\n")
    stream.write(f"After: {comparison.after_collected_at_utc}\n")
    stream.write(
        "Overall: "
        f"{comparison.before_overall_status.value} -> "
        f"{comparison.after_overall_status.value}\n"
    )
    for delta in comparison.deltas:
        before = delta.before_status.value if delta.before_status is not None else "-"
        after = delta.after_status.value if delta.after_status is not None else "-"
        fields = (
            f" fields={','.join(delta.changed_fields)}"
            if delta.changed_fields else ""
        )
        stream.write(
            f"{delta.kind.value:<16} {delta.check_id} "
            f"{before} -> {after}{fields}\n"
        )

    counts = {kind: 0 for kind in DeltaKind}
    for delta in comparison.deltas:
        counts[delta.kind] += 1
    stream.write(
        "\nSummary: "
        f"{comparison.total_checks} checks, "
        f"{comparison.unchanged_checks} unchanged, "
        f"{len(comparison.deltas)} changed "
        f"({counts[DeltaKind.ADDED]} added, "
        f"{counts[DeltaKind.REMOVED]} removed, "
        f"{counts[DeltaKind.STATUS_CHANGED]} status, "
        f"{counts[DeltaKind.EVIDENCE_CHANGED]} evidence); "
        f"comparisonExit={comparison.exit_code}\n"
    )
