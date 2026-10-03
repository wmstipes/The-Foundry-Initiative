"""Opt-in snapshot context for incident-brief/v1alpha2; entirely offline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
import json
from pathlib import Path
from typing import Any, TextIO

from .comparison import DeltaKind, EvidenceComparison, compare_evidence
from .constants import SCHEMA_VERSION
from .evidence import ValidatedEvidence
from .incident import (
    INCIDENT_LIMITATIONS, IncidentBrief, IncidentBriefError,
    _brief_object, _brief_status, _brief_string, _brief_timestamp,
    _reject_brief_constant, _unique_brief_object,
    build_incident_brief, parse_incident_brief_json,
    render_incident_brief_details, render_incident_brief_json,
)
from .models import Status
from .runbook_mapping import RunbookMapping


SNAPSHOT_BRIEF_SCHEMA = "forgeops.incident-brief/v1alpha2"
SNAPSHOT_BRIEF_INPUT_LIMIT = 1024 * 1024
COVERAGE_LIMITATION = (
    "Checks absent from both snapshots are not assessed. Optional HTTP and "
    "mesh/path coverage, and collection completeness, are not established."
)
SNAPSHOT_BRIEF_LIMITATIONS = INCIDENT_LIMITATIONS + (
    "Recovery applies only to supplied check identities; it does not establish complete collection coverage.",
    "Snapshot/comparison linkage establishes consistency, not artifact authenticity or trusted collection time.",
    "Saved briefs cannot recheck raw evidence changes. Runbook coverage remains delta-only.",
)
_FIELDS = (
    "schema", "evidenceSchema", "before", "after", "coverage", "assessment",
    "deltaBrief", "limitations",
)
_CONTEXT_FIELDS = ("collectedAtUtc", "summary", "checks")
_SUMMARY_FIELDS = ("pass", "warn", "fail", "unknown", "overallStatus", "exitCode")


class Recovery(StrEnum):
    NONE_ESTABLISHED = "NONE_ESTABLISHED"
    PARTIAL = "PARTIAL"
    COMPLETE_FOR_SUPPLIED_CHECKS = "COMPLETE_FOR_SUPPLIED_CHECKS"


@dataclass(frozen=True, slots=True)
class SnapshotCheck:
    check_id: str
    status: Status


@dataclass(frozen=True, slots=True)
class SnapshotContext:
    collected_at_utc: str
    checks: tuple[SnapshotCheck, ...]

    @property
    def overall_status(self) -> Status:
        return next(
            (status for status in (Status.UNKNOWN, Status.FAIL, Status.WARN)
             if any(check.status is status for check in self.checks)),
            Status.PASS,
        )

    @property
    def summary(self) -> dict[str, Any]:
        return {
            **{status.value.lower(): sum(c.status is status for c in self.checks) for status in Status},
            "overallStatus": self.overall_status.value,
            "exitCode": (2 if self.overall_status is Status.UNKNOWN else
                         0 if self.overall_status is Status.PASS else 1),
        }


@dataclass(frozen=True, slots=True)
class SnapshotIncidentBrief:
    before: SnapshotContext
    after: SnapshotContext
    delta_brief: IncidentBrief

    @property
    def coverage(self) -> dict[str, Any]:
        before = {c.check_id for c in self.before.checks}
        after = {c.check_id for c in self.after.checks}
        return {
            "completeness": "NOT_ESTABLISHED",
            "addedCheckIds": sorted(after - before),
            "removedCheckIds": sorted(before - after),
            "limitations": [COVERAGE_LIMITATION],
        }

    @property
    def assessment(self) -> dict[str, Any]:
        before = {c.check_id: c.status for c in self.before.checks}
        after = {c.check_id: c.status for c in self.after.checks}
        common = before.keys() & after.keys()
        recovered = sorted(
            key for key in common
            if before[key] in (Status.WARN, Status.FAIL) and after[key] is Status.PASS
        )
        regained = sorted(
            key for key in common if before[key] is Status.UNKNOWN and after[key] is not Status.UNKNOWN
        )
        remaining = sorted(key for key in after if after[key] is not Status.PASS)
        recovery = Recovery.NONE_ESTABLISHED
        if recovered:
            recovery = (
                Recovery.COMPLETE_FOR_SUPPLIED_CHECKS
                if before.keys() == after.keys() and not remaining else Recovery.PARTIAL
            )
        return {
            "recovery": recovery.value,
            "knownRecoveredCheckIds": recovered,
            "regainedEvidenceCheckIds": regained,
            "remainingNonPassingCheckIds": remaining,
        }


def _fail(code: str, summary: str) -> None:
    raise IncidentBriefError(code, summary)


def _same_json(actual: Any, expected: Any) -> bool:
    # JSON equality must distinguish booleans and floats from integer counts.
    try:
        return json.dumps(actual, ensure_ascii=True) == json.dumps(expected, ensure_ascii=True)
    except (ValueError, RecursionError):
        return False


def _context_document(context: SnapshotContext) -> dict[str, Any]:
    return {
        "collectedAtUtc": context.collected_at_utc,
        "summary": context.summary,
        "checks": [{"id": c.check_id, "status": c.status.value} for c in context.checks],
    }


def _document(brief: SnapshotIncidentBrief) -> dict[str, Any]:
    delta = StringIO()
    render_incident_brief_json(brief.delta_brief, delta)
    return {
        "schema": SNAPSHOT_BRIEF_SCHEMA,
        "evidenceSchema": SCHEMA_VERSION,
        "before": _context_document(brief.before),
        "after": _context_document(brief.after),
        "coverage": brief.coverage,
        "assessment": brief.assessment,
        "deltaBrief": json.loads(delta.getvalue()),
        "limitations": list(SNAPSHOT_BRIEF_LIMITATIONS),
    }


def _encode(brief: SnapshotIncidentBrief) -> bytes:
    raw = (json.dumps(_document(brief), ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    if len(raw) > SNAPSHOT_BRIEF_INPUT_LIMIT:
        _fail("oversized-input", "snapshot incident brief exceeds the 1 MiB limit")
    return raw


def _parse_context(value: Any) -> SnapshotContext:
    value = _brief_object(value, _CONTEXT_FIELDS, "snapshot context")
    timestamp = _brief_timestamp(value["collectedAtUtc"], "collectedAtUtc")
    if not isinstance(value["checks"], list) or not value["checks"]:
        _fail("contract-type", "snapshot checks must be a non-empty array")
    checks: list[SnapshotCheck] = []
    for item in value["checks"]:
        item = _brief_object(item, ("id", "status"), "snapshot check")
        checks.append(SnapshotCheck(_brief_string(item["id"], "id"), _brief_status(item["status"], "status")))
    identifiers = [c.check_id for c in checks]
    if identifiers != sorted(set(identifiers)):
        _fail("contract-order", "snapshot check identifiers must be unique and sorted")
    context = SnapshotContext(timestamp, tuple(checks))
    summary = _brief_object(value["summary"], _SUMMARY_FIELDS, "snapshot summary")
    if not _same_json(summary, context.summary):
        _fail("inconsistent-summary", "snapshot summary does not match its check statuses")
    return context


def _validate_context_linkage(brief: SnapshotIncidentBrief) -> None:
    delta = brief.delta_brief
    if (
        brief.before.collected_at_utc != delta.before_collected_at_utc
        or brief.after.collected_at_utc != delta.after_collected_at_utc
    ):
        _fail("window-mismatch", "snapshot context and delta windows do not match")
    before = {c.check_id: c.status for c in brief.before.checks}
    after = {c.check_id: c.status for c in brief.after.checks}
    required = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    fact_ids = {fact.check_id for fact in delta.facts}
    if not required <= fact_ids:
        _fail("context-mismatch", "delta facts omit a snapshot status or identity change")
    for fact in delta.facts:
        key = fact.check_id
        if (key not in before and key not in after) or (
            fact.before_status is not before.get(key) or fact.after_status is not after.get(key)
        ):
            _fail("context-mismatch", "delta fact statuses do not match snapshot context")
        expected_kind = (
            DeltaKind.ADDED if key not in before else
            DeltaKind.REMOVED if key not in after else
            DeltaKind.STATUS_CHANGED if before[key] is not after[key] else DeltaKind.EVIDENCE_CHANGED
        )
        if fact.delta_kind is not expected_kind:
            _fail("context-mismatch", "delta fact kind does not match snapshot context")


def parse_snapshot_brief_json(raw: bytes) -> SnapshotIncidentBrief:
    """Strictly load the opt-in contract without changing legacy interpretation."""
    if len(raw) > SNAPSHOT_BRIEF_INPUT_LIMIT:
        _fail("oversized-input", "snapshot incident brief exceeds the 1 MiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("invalid-utf8", "snapshot incident brief must be UTF-8")
    try:
        value = json.loads(text, object_pairs_hook=_unique_brief_object, parse_constant=_reject_brief_constant)
    except IncidentBriefError:
        raise
    except (ValueError, RecursionError):
        _fail("malformed-json", "snapshot incident brief must be one bounded JSON document")
    value = _brief_object(value, _FIELDS, "snapshot incident brief")
    if value["schema"] != SNAPSHOT_BRIEF_SCHEMA or value["evidenceSchema"] != SCHEMA_VERSION:
        _fail("unsupported-schema", "snapshot incident brief schema is not supported")
    before, after = _parse_context(value["before"]), _parse_context(value["after"])
    delta = parse_incident_brief_json(json.dumps(value["deltaBrief"], ensure_ascii=True).encode("utf-8"))
    brief = SnapshotIncidentBrief(before, after, delta)
    _validate_context_linkage(brief)
    if not _same_json(value["coverage"], brief.coverage):
        _fail("inconsistent-coverage", "coverage does not match the supplied check identities")
    if not _same_json(value["assessment"], brief.assessment):
        _fail("inconsistent-assessment", "assessment does not match the supplied check statuses")
    if value["limitations"] != list(SNAPSHOT_BRIEF_LIMITATIONS):
        _fail("contract-value", "snapshot incident brief limitations do not match")
    return brief


def load_snapshot_brief(path_text: str) -> SnapshotIncidentBrief:
    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _fail("input-unavailable", "snapshot incident brief is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(SNAPSHOT_BRIEF_INPUT_LIMIT + 1)
    except IncidentBriefError:
        raise
    except OSError:
        _fail("input-unavailable", "snapshot incident brief is not an accessible regular file")
    return parse_snapshot_brief_json(raw)


def build_snapshot_incident_brief(
    before: ValidatedEvidence, after: ValidatedEvidence,
    comparison: EvidenceComparison, mapping: RunbookMapping,
) -> SnapshotIncidentBrief:
    if compare_evidence(before, after) != comparison:
        _fail("snapshot-comparison-mismatch", "comparison does not match the supplied snapshots")
    def context(evidence: ValidatedEvidence) -> SnapshotContext:
        return SnapshotContext(
            evidence.snapshot.collected_at_utc,
            tuple(SnapshotCheck(c.check_id, c.status) for c in sorted(evidence.snapshot.checks, key=lambda c: c.check_id)),
        )
    brief = SnapshotIncidentBrief(context(before), context(after), build_incident_brief(comparison, mapping))
    # Apply the same strict semantics and size bounds before any output is emitted.
    return parse_snapshot_brief_json(_encode(brief))


def render_snapshot_brief_json(brief: SnapshotIncidentBrief, stream: TextIO) -> None:
    stream.write(_encode(brief).decode("utf-8"))


def render_snapshot_brief_text(brief: SnapshotIncidentBrief, stream: TextIO) -> None:
    stream.write("ForgeOps incident brief with snapshot context\n")
    stream.write(f"Supplied window: {brief.before.collected_at_utc} -> {brief.after.collected_at_utc}\n")
    for label, context in (("Before", brief.before), ("After", brief.after)):
        counts = ", ".join(f"{context.summary[s.value.lower()]} {s.value}" for s in Status)
        stream.write(f"{label} snapshot: {context.overall_status.value} ({counts})\n")
    assessment, coverage = brief.assessment, brief.coverage
    stream.write(f"Recovery: {assessment['recovery']} (supplied checks only)\n")
    stream.write(f"Delta state: {brief.delta_brief.state.value} (changed checks only)\n")
    stream.write("\nRemaining non-passing checks (including unchanged checks)\n")
    remaining = [c for c in brief.after.checks if c.status is not Status.PASS]
    if not remaining:
        stream.write("- none in supplied after snapshot\n")
    for check in remaining:
        stream.write(f"- {check.check_id}: {check.status.value}\n")
    for label, identifiers in (
        ("Known WARN/FAIL-to-PASS recovery", assessment["knownRecoveredCheckIds"]),
        ("Regained evidence (UNKNOWN to a known status; not proof of recovery)", assessment["regainedEvidenceCheckIds"]),
        ("Added check identities", coverage["addedCheckIds"]),
        ("Removed check identities", coverage["removedCheckIds"]),
    ):
        stream.write(f"\n{label}\n")
        for check_id in identifiers:
            stream.write(f"- {check_id}\n")
        if not identifiers:
            stream.write("- none\n")
    stream.write(f"\nCollection completeness: {coverage['completeness']}\n{COVERAGE_LIMITATION}\n")
    stream.write("\nDelta details and references (mapping covers changed checks only)\n")
    render_incident_brief_details(brief.delta_brief, stream)
    stream.write("\nSnapshot context limitations\n")
    for limitation in SNAPSHOT_BRIEF_LIMITATIONS[len(INCIDENT_LIMITATIONS):]:
        stream.write(f"- {limitation}\n")
