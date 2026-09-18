"""Deterministic comparison of contract-validated ForgeOps evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, TextIO

from .constants import SCHEMA_VERSION
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


COMPARISON_SCHEMA = "forgeops.comparison/v1alpha1"
COMPARISON_INPUT_LIMIT = 256 * 1024
COMPARISON_LIMITATION = (
    "This deterministic comparison reports validated field differences only; "
    "it does not establish provenance, operational severity, causation, "
    "diagnosis, or recommendation."
)


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
_COMPARISON_FIELDS = (
    "schema",
    "evidenceSchema",
    "beforeCollectedAtUtc",
    "afterCollectedAtUtc",
    "beforeOverallStatus",
    "afterOverallStatus",
    "summary",
    "deltas",
    "limitations",
)
_SUMMARY_FIELDS = (
    "totalChecks",
    "unchangedChecks",
    "changedChecks",
    "added",
    "removed",
    "statusChanged",
    "evidenceChanged",
    "comparisonExit",
)
_DELTA_FIELDS = (
    "id", "kind", "beforeStatus", "afterStatus", "changedFields",
)


class ComparisonValidationError(ValueError):
    """A bounded, non-sensitive serialized-comparison failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _validation_fail(code: str, summary: str) -> None:
    raise ComparisonValidationError(code, summary)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _validation_fail(
                "duplicate-key", "comparison objects must not contain duplicate keys",
            )
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    _validation_fail("malformed-json", "comparison must use standard JSON values")


def _require_fields(
    value: Any,
    fields: tuple[str, ...],
    scope: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or tuple(value) != fields:
        _validation_fail(
            "contract-fields", f"{scope} fields or field order are unsupported",
        )
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _validation_fail("contract-type", f"{field} must be a non-empty string")
    return value


def _require_status(value: Any, field: str) -> Status:
    try:
        return Status(_require_string(value, field))
    except ValueError:
        _validation_fail("contract-status", f"{field} is not supported")


def _require_count(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        _validation_fail("contract-type", f"summary.{field} must be non-negative")
    return value


def _require_timestamp(value: Any, field: str) -> str:
    timestamp = _require_string(value, field)
    try:
        _timestamp(timestamp)
    except ValueError:
        _validation_fail("contract-timestamp", f"{field} must use RFC 3339 UTC seconds")
    return timestamp


def _optional_status(value: Any, field: str) -> Status | None:
    return None if value is None else _require_status(value, field)


def parse_comparison_json(raw: bytes) -> EvidenceComparison:
    """Strictly load one deterministic forgeops.comparison/v1alpha1 document."""

    if len(raw) > COMPARISON_INPUT_LIMIT:
        _validation_fail("oversized-input", "comparison exceeds the 256 KiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _validation_fail("invalid-utf8", "comparison must be UTF-8")
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except ComparisonValidationError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _validation_fail("malformed-json", "comparison must be one bounded JSON document")

    document = _require_fields(decoded, _COMPARISON_FIELDS, "top-level")
    if document["schema"] != COMPARISON_SCHEMA:
        _validation_fail("unsupported-schema", "comparison schema is not supported")
    if document["evidenceSchema"] != SCHEMA_VERSION:
        _validation_fail("unsupported-evidence-schema", "evidence schema is not supported")
    before_time = _require_timestamp(
        document["beforeCollectedAtUtc"], "beforeCollectedAtUtc",
    )
    after_time = _require_timestamp(
        document["afterCollectedAtUtc"], "afterCollectedAtUtc",
    )
    if _timestamp(after_time) < _timestamp(before_time):
        _validation_fail("reversed-chronology", "comparison chronology is reversed")
    before_overall = _require_status(
        document["beforeOverallStatus"], "beforeOverallStatus",
    )
    after_overall = _require_status(
        document["afterOverallStatus"], "afterOverallStatus",
    )

    raw_deltas = document["deltas"]
    if not isinstance(raw_deltas, list):
        _validation_fail("contract-type", "deltas must be an array")
    deltas: list[CheckDelta] = []
    identifiers: list[str] = []
    allowed_fields = tuple(field for field, _ in _COMPARED_FIELDS)
    for index, raw_delta in enumerate(raw_deltas):
        delta = _require_fields(raw_delta, _DELTA_FIELDS, f"deltas[{index}]")
        check_id = _require_string(delta["id"], f"deltas[{index}].id")
        identifiers.append(check_id)
        try:
            kind = DeltaKind(_require_string(delta["kind"], f"deltas[{index}].kind"))
        except ValueError:
            _validation_fail("contract-kind", "delta kind is not supported")
        before_status = _optional_status(
            delta["beforeStatus"], f"deltas[{index}].beforeStatus",
        )
        after_status = _optional_status(
            delta["afterStatus"], f"deltas[{index}].afterStatus",
        )
        fields_value = delta["changedFields"]
        if not isinstance(fields_value, list) or not all(
            isinstance(field, str) for field in fields_value
        ):
            _validation_fail("contract-type", "changedFields must be a string array")
        changed_fields = tuple(fields_value)
        if (
            len(set(changed_fields)) != len(changed_fields)
            or any(field not in allowed_fields for field in changed_fields)
            or changed_fields != tuple(
                field for field in allowed_fields if field in changed_fields
            )
        ):
            _validation_fail("contract-fields", "changedFields are unsupported or unordered")
        if kind is DeltaKind.ADDED:
            valid_shape = before_status is None and after_status is not None and not changed_fields
        elif kind is DeltaKind.REMOVED:
            valid_shape = before_status is not None and after_status is None and not changed_fields
        elif kind is DeltaKind.STATUS_CHANGED:
            valid_shape = (
                before_status is not None
                and after_status is not None
                and before_status is not after_status
                and "status" in changed_fields
            )
        else:
            valid_shape = (
                before_status is not None
                and before_status is after_status
                and bool(changed_fields)
                and "status" not in changed_fields
            )
        if not valid_shape:
            _validation_fail("contract-delta", "delta fields do not match its kind")
        deltas.append(CheckDelta(
            check_id, kind, before_status, after_status, changed_fields,
        ))
    if identifiers != sorted(set(identifiers)):
        _validation_fail("contract-order", "delta identifiers must be unique and sorted")

    summary = _require_fields(document["summary"], _SUMMARY_FIELDS, "summary")
    counts = {field: _require_count(summary[field], field) for field in _SUMMARY_FIELDS}
    expected_kind_counts = {
        "added": sum(delta.kind is DeltaKind.ADDED for delta in deltas),
        "removed": sum(delta.kind is DeltaKind.REMOVED for delta in deltas),
        "statusChanged": sum(delta.kind is DeltaKind.STATUS_CHANGED for delta in deltas),
        "evidenceChanged": sum(delta.kind is DeltaKind.EVIDENCE_CHANGED for delta in deltas),
    }
    if counts["changedChecks"] != len(deltas):
        _validation_fail("inconsistent-summary", "changedChecks does not match deltas")
    if any(counts[field] != expected for field, expected in expected_kind_counts.items()):
        _validation_fail("inconsistent-summary", "delta counts do not match deltas")
    if counts["totalChecks"] != counts["unchangedChecks"] + len(deltas):
        _validation_fail("inconsistent-summary", "totalChecks does not match comparison counts")
    expected_exit = 1 if deltas else 0
    if counts["comparisonExit"] != expected_exit:
        _validation_fail("inconsistent-summary", "comparisonExit does not match deltas")
    if document["limitations"] != [COMPARISON_LIMITATION]:
        _validation_fail("contract-value", "comparison limitations do not match")

    return EvidenceComparison(
        schema=SCHEMA_VERSION,
        before_collected_at_utc=before_time,
        after_collected_at_utc=after_time,
        before_overall_status=before_overall,
        after_overall_status=after_overall,
        total_checks=counts["totalChecks"],
        unchanged_checks=counts["unchangedChecks"],
        deltas=tuple(deltas),
    )


def load_comparison_file(path_text: str) -> EvidenceComparison:
    """Read one explicit regular comparison file and validate its contract."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _validation_fail(
                "input-unavailable", "comparison is not an accessible regular file",
            )
        with path.open("rb") as stream:
            raw = stream.read(COMPARISON_INPUT_LIMIT + 1)
    except ComparisonValidationError:
        raise
    except OSError:
        _validation_fail(
            "input-unavailable", "comparison is not an accessible regular file",
        )
    return parse_comparison_json(raw)


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


def _delta_counts(comparison: EvidenceComparison) -> dict[DeltaKind, int]:
    counts = {kind: 0 for kind in DeltaKind}
    for delta in comparison.deltas:
        counts[delta.kind] += 1
    return counts


def render_comparison_json(comparison: EvidenceComparison, stream: TextIO) -> None:
    """Render one deterministic, disclosure-minimized comparison document."""

    counts = _delta_counts(comparison)
    value = {
        "schema": COMPARISON_SCHEMA,
        "evidenceSchema": comparison.schema,
        "beforeCollectedAtUtc": comparison.before_collected_at_utc,
        "afterCollectedAtUtc": comparison.after_collected_at_utc,
        "beforeOverallStatus": comparison.before_overall_status.value,
        "afterOverallStatus": comparison.after_overall_status.value,
        "summary": {
            "totalChecks": comparison.total_checks,
            "unchangedChecks": comparison.unchanged_checks,
            "changedChecks": len(comparison.deltas),
            "added": counts[DeltaKind.ADDED],
            "removed": counts[DeltaKind.REMOVED],
            "statusChanged": counts[DeltaKind.STATUS_CHANGED],
            "evidenceChanged": counts[DeltaKind.EVIDENCE_CHANGED],
            "comparisonExit": comparison.exit_code,
        },
        "deltas": [
            {
                "id": delta.check_id,
                "kind": delta.kind.value,
                "beforeStatus": (
                    delta.before_status.value
                    if delta.before_status is not None else None
                ),
                "afterStatus": (
                    delta.after_status.value
                    if delta.after_status is not None else None
                ),
                "changedFields": list(delta.changed_fields),
            }
            for delta in comparison.deltas
        ],
        "limitations": [COMPARISON_LIMITATION],
    }
    json.dump(value, stream, ensure_ascii=True, indent=2)
    stream.write("\n")
