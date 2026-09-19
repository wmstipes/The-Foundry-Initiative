"""Deterministic, artifact-bounded ForgeOps incident briefs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path, PurePosixPath
from typing import Any, TextIO

from .comparison import CheckDelta, DeltaKind, EvidenceComparison
from .models import Status
from .runbook_mapping import RunbookMapping, RunbookMatch


INCIDENT_BRIEF_SCHEMA = "forgeops.incident-brief/v1alpha1"
INCIDENT_BRIEF_INPUT_LIMIT = 256 * 1024
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


_BRIEF_FIELDS = (
    "schema", "comparisonSchema", "mappingSchema", "beforeCollectedAtUtc",
    "afterCollectedAtUtc", "state", "facts", "runbooks", "unmappedDeltaIds",
    "uncertainties", "limitations",
)
_FACT_FIELDS = ("id", "kind", "beforeStatus", "afterStatus")
_RUNBOOK_FIELDS = ("runbookId", "title", "path", "section", "reasons")
_REASON_FIELDS = ("checkId", "deltaKind", "afterStatus")


def _brief_fail(code: str, summary: str) -> None:
    raise IncidentBriefError(code, summary)


def _unique_brief_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _brief_fail("duplicate-key", "brief objects must not contain duplicate keys")
        value[key] = item
    return value


def _reject_brief_constant(_: str) -> None:
    _brief_fail("malformed-json", "brief must use standard JSON values")


def _brief_object(value: Any, fields: tuple[str, ...], scope: str) -> dict[str, Any]:
    if not isinstance(value, dict) or tuple(value) != fields:
        _brief_fail("contract-fields", f"{scope} fields or field order are unsupported")
    return value


def _brief_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _brief_fail("contract-type", f"{field} must be a non-empty string")
    return value


def _brief_status(value: Any, field: str) -> Status:
    try:
        return Status(_brief_string(value, field))
    except ValueError:
        _brief_fail("contract-status", f"{field} is not supported")


def _optional_brief_status(value: Any, field: str) -> Status | None:
    return None if value is None else _brief_status(value, field)


def _brief_timestamp(value: Any, field: str) -> str:
    from .comparison import _timestamp

    timestamp = _brief_string(value, field)
    try:
        _timestamp(timestamp)
    except ValueError:
        _brief_fail("contract-timestamp", f"{field} must use RFC 3339 UTC seconds")
    return timestamp


def _brief_path(value: Any) -> str:
    path = _brief_string(value, "runbook.path")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or ".." in parsed.parts
        or parsed.suffix != ".md"
        or parsed.parts[:2] != ("docs", "runbooks")
    ):
        _brief_fail(
            "contract-path",
            "brief runbook path must be a repository-relative Markdown path under docs/runbooks",
        )
    return path


def _string_array(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        _brief_fail("contract-type", f"{field} must be a string array")
    result = tuple(value)
    if result != tuple(sorted(set(result))):
        _brief_fail("contract-order", f"{field} must be unique and sorted")
    return result


def parse_incident_brief_json(raw: bytes) -> IncidentBrief:
    """Strictly parse one deterministic incident-brief document."""

    if len(raw) > INCIDENT_BRIEF_INPUT_LIMIT:
        _brief_fail("oversized-input", "incident brief exceeds the 256 KiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _brief_fail("invalid-utf8", "incident brief must be UTF-8")
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_brief_object,
            parse_constant=_reject_brief_constant,
        )
    except IncidentBriefError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _brief_fail("malformed-json", "incident brief must be one bounded JSON document")

    document = _brief_object(decoded, _BRIEF_FIELDS, "top-level")
    if document["schema"] != INCIDENT_BRIEF_SCHEMA:
        _brief_fail("unsupported-schema", "incident brief schema is not supported")
    if document["comparisonSchema"] != "forgeops.comparison/v1alpha1":
        _brief_fail("unsupported-comparison-schema", "comparison schema is not supported")
    if document["mappingSchema"] != "forgeops.runbook-mapping/v1alpha1":
        _brief_fail("unsupported-mapping-schema", "mapping schema is not supported")
    before_time = _brief_timestamp(document["beforeCollectedAtUtc"], "beforeCollectedAtUtc")
    after_time = _brief_timestamp(document["afterCollectedAtUtc"], "afterCollectedAtUtc")
    from .comparison import _timestamp
    if _timestamp(after_time) < _timestamp(before_time):
        _brief_fail("reversed-chronology", "incident brief chronology is reversed")
    try:
        state = IncidentState(_brief_string(document["state"], "state"))
    except ValueError:
        _brief_fail("contract-state", "incident state is not supported")

    raw_facts = document["facts"]
    if not isinstance(raw_facts, list):
        _brief_fail("contract-type", "facts must be an array")
    facts: list[IncidentFact] = []
    fact_ids: list[str] = []
    for index, raw_fact in enumerate(raw_facts):
        fact = _brief_object(raw_fact, _FACT_FIELDS, f"facts[{index}]")
        check_id = _brief_string(fact["id"], f"facts[{index}].id")
        try:
            kind = DeltaKind(_brief_string(fact["kind"], f"facts[{index}].kind"))
        except ValueError:
            _brief_fail("contract-kind", "fact kind is not supported")
        before_status = _optional_brief_status(fact["beforeStatus"], "fact.beforeStatus")
        after_status = _optional_brief_status(fact["afterStatus"], "fact.afterStatus")
        if kind is DeltaKind.ADDED:
            valid_shape = before_status is None and after_status is not None
        elif kind is DeltaKind.REMOVED:
            valid_shape = before_status is not None and after_status is None
        elif kind is DeltaKind.STATUS_CHANGED:
            valid_shape = before_status is not None and after_status is not None and before_status is not after_status
        else:
            valid_shape = before_status is not None and before_status is after_status
        if not valid_shape:
            _brief_fail("contract-fact", "fact statuses do not match its kind")
        fact_ids.append(check_id)
        facts.append(IncidentFact(check_id, kind, before_status, after_status))
    if fact_ids != sorted(set(fact_ids)):
        _brief_fail("contract-order", "fact identifiers must be unique and sorted")

    raw_runbooks = document["runbooks"]
    if not isinstance(raw_runbooks, list):
        _brief_fail("contract-type", "runbooks must be an array")
    runbooks: list[RunbookMatch] = []
    runbook_ids: list[str] = []
    mapped_ids: set[str] = set()
    fact_by_id = {fact.check_id: fact for fact in facts}
    from .runbook_mapping import MappingReason
    for runbook_index, raw_runbook in enumerate(raw_runbooks):
        runbook = _brief_object(raw_runbook, _RUNBOOK_FIELDS, f"runbooks[{runbook_index}]")
        runbook_id = _brief_string(runbook["runbookId"], "runbook.runbookId")
        runbook_ids.append(runbook_id)
        raw_reasons = runbook["reasons"]
        if not isinstance(raw_reasons, list) or not raw_reasons:
            _brief_fail("contract-type", "runbook reasons must be a non-empty array")
        reasons: list[MappingReason] = []
        reason_ids: list[str] = []
        for reason_index, raw_reason in enumerate(raw_reasons):
            reason = _brief_object(raw_reason, _REASON_FIELDS, f"runbook reasons[{reason_index}]")
            check_id = _brief_string(reason["checkId"], "reason.checkId")
            try:
                kind = DeltaKind(_brief_string(reason["deltaKind"], "reason.deltaKind"))
            except ValueError:
                _brief_fail("contract-kind", "reason delta kind is not supported")
            after_status = _brief_status(reason["afterStatus"], "reason.afterStatus")
            fact = fact_by_id.get(check_id)
            if fact is None or fact.delta_kind is not kind or fact.after_status is not after_status:
                _brief_fail("contract-reason", "runbook reason does not match a brief fact")
            reason_ids.append(check_id)
            mapped_ids.add(check_id)
            reasons.append(MappingReason(check_id, kind.value, after_status))
        if reason_ids != sorted(set(reason_ids)):
            _brief_fail("contract-order", "runbook reasons must be unique and sorted")
        runbooks.append(RunbookMatch(
            runbook_id,
            _brief_string(runbook["title"], "runbook.title"),
            _brief_path(runbook["path"]),
            _brief_string(runbook["section"], "runbook.section"),
            tuple(reasons),
        ))
    if runbook_ids != sorted(set(runbook_ids)):
        _brief_fail("contract-order", "runbook identifiers must be unique and sorted")

    unmapped = _string_array(document["unmappedDeltaIds"], "unmappedDeltaIds")
    if set(unmapped) != set(fact_ids) - mapped_ids or mapped_ids & set(unmapped):
        _brief_fail("contract-coverage", "brief mapping coverage does not match its facts")
    uncertainties = _string_array(document["uncertainties"], "uncertainties")

    comparison = EvidenceComparison(
        "forgeops.snapshot/v1alpha1",
        before_time,
        after_time,
        Status.PASS,
        Status.PASS,
        len(facts),
        0,
        tuple(
            CheckDelta(
                fact.check_id,
                fact.delta_kind,
                fact.before_status,
                fact.after_status,
                (("status",) if fact.delta_kind is DeltaKind.STATUS_CHANGED else
                 ("observation",) if fact.delta_kind is DeltaKind.EVIDENCE_CHANGED else ()),
            )
            for fact in facts
        ),
    )
    expected_state = classify_incident_state(comparison)
    if state is not expected_state:
        _brief_fail("inconsistent-state", "incident state does not match its facts")
    expected_uncertainties = {"point-in-time-only"}
    if facts:
        expected_uncertainties.add("cause-not-established")
    if state is IncidentState.INCOMPLETE:
        expected_uncertainties.add("evidence-incomplete")
    if unmapped:
        expected_uncertainties.add("mapping-incomplete")
    if uncertainties != tuple(sorted(expected_uncertainties)):
        _brief_fail("inconsistent-uncertainty", "uncertainties do not match the brief contents")
    if document["limitations"] != list(INCIDENT_LIMITATIONS):
        _brief_fail("contract-value", "incident brief limitations do not match")

    return IncidentBrief(
        before_time, after_time, state, tuple(facts), tuple(runbooks), unmapped, uncertainties,
    )


def load_incident_brief(path_text: str) -> IncidentBrief:
    """Read and validate one explicitly selected regular incident-brief file."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _brief_fail("input-unavailable", "incident brief is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(INCIDENT_BRIEF_INPUT_LIMIT + 1)
    except IncidentBriefError:
        raise
    except OSError:
        _brief_fail("input-unavailable", "incident brief is not an accessible regular file")
    return parse_incident_brief_json(raw)


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


def render_incident_brief_text(brief: IncidentBrief, stream: TextIO) -> None:
    """Render the same bounded brief model for deterministic human review."""

    stream.write("ForgeOps incident brief\n")
    stream.write(
        f"Supplied window: {brief.before_collected_at_utc} -> "
        f"{brief.after_collected_at_utc}\n"
    )
    stream.write(f"Bounded state: {brief.state.value}\n")

    stream.write("\nDeterministic facts\n")
    if not brief.facts:
        stream.write("- none\n")
    for fact in brief.facts:
        before = fact.before_status.value if fact.before_status is not None else "-"
        after = fact.after_status.value if fact.after_status is not None else "-"
        stream.write(
            f"- {fact.check_id}: {fact.delta_kind.value} {before} -> {after}\n"
        )

    stream.write("\nCataloged runbook references (informational only)\n")
    if not brief.runbooks:
        stream.write("- none\n")
    for runbook in brief.runbooks:
        stream.write(
            f"- {runbook.runbook_id}: {runbook.title} "
            f"[{runbook.path}#{runbook.section}]\n"
        )
        for reason in runbook.reasons:
            stream.write(
                f"  matched rule: {reason.check_id} {reason.delta_kind} "
                f"after={reason.after_status.value}\n"
            )

    stream.write("\nUnmapped deltas\n")
    if not brief.unmapped_delta_ids:
        stream.write("- none\n")
    for check_id in brief.unmapped_delta_ids:
        stream.write(f"- {check_id}\n")

    stream.write("\nUncertainty\n")
    for uncertainty in brief.uncertainties:
        stream.write(f"- {uncertainty}\n")

    stream.write("\nAuthority limitations\n")
    for limitation in INCIDENT_LIMITATIONS:
        stream.write(f"- {limitation}\n")
