"""Deterministic offline mapping from comparison deltas to runbook knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Any, TextIO

from .comparison import CheckDelta, DeltaKind, EvidenceComparison
from .models import Status
from .runbooks import RunbookCatalog, RunbookEntry, RunbookSignal


RUNBOOK_MAPPING_SCHEMA = "forgeops.runbook-mapping/v1alpha1"
RUNBOOK_MAPPING_INPUT_LIMIT = 256 * 1024
RUNBOOK_MAPPING_LIMITATION = (
    "This deterministic mapping reports catalog rules matched by comparison "
    "deltas; it does not establish causation, operational severity, diagnosis, "
    "recommendation, or remediation authority."
)


class RunbookMappingError(ValueError):
    """A bounded, non-sensitive serialized-mapping validation failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


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


_TOP_LEVEL_FIELDS = (
    "schema", "comparisonSchema", "beforeCollectedAtUtc", "afterCollectedAtUtc",
    "summary", "matches", "unmappedDeltaIds", "limitations",
)
_SUMMARY_FIELDS = (
    "totalDeltas", "mappedDeltas", "unmappedDeltas", "runbookMatches", "mappingExit",
)
_MATCH_FIELDS = ("runbookId", "title", "path", "section", "reasons")
_REASON_FIELDS = ("checkId", "deltaKind", "afterStatus")


def _mapping_fail(code: str, summary: str) -> None:
    raise RunbookMappingError(code, summary)


def _unique_mapping_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _mapping_fail("duplicate-key", "mapping objects must not contain duplicate keys")
        value[key] = item
    return value


def _reject_mapping_constant(_: str) -> None:
    _mapping_fail("malformed-json", "mapping must use standard JSON values")


def _mapping_object(value: Any, fields: tuple[str, ...], scope: str) -> dict[str, Any]:
    if not isinstance(value, dict) or tuple(value) != fields:
        _mapping_fail("contract-fields", f"{scope} fields or field order are unsupported")
    return value


def _mapping_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _mapping_fail("contract-type", f"{field} must be a non-empty string")
    return value


def _mapping_count(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        _mapping_fail("contract-type", f"summary.{field} must be non-negative")
    return value


def _mapping_timestamp(value: Any, field: str) -> str:
    from .comparison import _timestamp

    timestamp = _mapping_string(value, field)
    try:
        _timestamp(timestamp)
    except ValueError:
        _mapping_fail("contract-timestamp", f"{field} must use RFC 3339 UTC seconds")
    return timestamp


def _mapping_path(value: Any) -> str:
    path = _mapping_string(value, "match.path")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or ".." in parsed.parts
        or parsed.suffix != ".md"
        or parsed.parts[:2] != ("docs", "runbooks")
    ):
        _mapping_fail(
            "contract-path",
            "mapping path must be a repository-relative Markdown path under docs/runbooks",
        )
    return path


def parse_runbook_mapping_json(raw: bytes) -> RunbookMapping:
    """Strictly parse one disclosure-bounded runbook mapping document."""

    if len(raw) > RUNBOOK_MAPPING_INPUT_LIMIT:
        _mapping_fail("oversized-input", "runbook mapping exceeds the 256 KiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _mapping_fail("invalid-utf8", "runbook mapping must be UTF-8")
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_mapping_object,
            parse_constant=_reject_mapping_constant,
        )
    except RunbookMappingError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _mapping_fail("malformed-json", "runbook mapping must be one bounded JSON document")

    document = _mapping_object(decoded, _TOP_LEVEL_FIELDS, "top-level")
    if document["schema"] != RUNBOOK_MAPPING_SCHEMA:
        _mapping_fail("unsupported-schema", "runbook mapping schema is not supported")
    if document["comparisonSchema"] != "forgeops.comparison/v1alpha1":
        _mapping_fail("unsupported-comparison-schema", "comparison schema is not supported")
    before_time = _mapping_timestamp(document["beforeCollectedAtUtc"], "beforeCollectedAtUtc")
    after_time = _mapping_timestamp(document["afterCollectedAtUtc"], "afterCollectedAtUtc")
    from .comparison import _timestamp
    if _timestamp(after_time) < _timestamp(before_time):
        _mapping_fail("reversed-chronology", "mapping chronology is reversed")

    raw_matches = document["matches"]
    if not isinstance(raw_matches, list):
        _mapping_fail("contract-type", "matches must be an array")
    matches: list[RunbookMatch] = []
    match_ids: list[str] = []
    all_reason_ids: list[str] = []
    for match_index, raw_match in enumerate(raw_matches):
        match = _mapping_object(raw_match, _MATCH_FIELDS, f"matches[{match_index}]")
        runbook_id = _mapping_string(match["runbookId"], f"matches[{match_index}].runbookId")
        match_ids.append(runbook_id)
        raw_reasons = match["reasons"]
        if not isinstance(raw_reasons, list) or not raw_reasons:
            _mapping_fail("contract-type", "match reasons must be a non-empty array")
        reasons: list[MappingReason] = []
        reason_ids: list[str] = []
        for reason_index, raw_reason in enumerate(raw_reasons):
            reason = _mapping_object(
                raw_reason,
                _REASON_FIELDS,
                f"matches[{match_index}].reasons[{reason_index}]",
            )
            check_id = _mapping_string(reason["checkId"], "reason.checkId")
            try:
                delta_kind = DeltaKind(_mapping_string(reason["deltaKind"], "reason.deltaKind"))
                after_status = Status(_mapping_string(reason["afterStatus"], "reason.afterStatus"))
            except ValueError:
                _mapping_fail("contract-value", "mapping reason contains an unsupported value")
            if delta_kind is DeltaKind.REMOVED:
                _mapping_fail("contract-reason", "removed deltas cannot have an after status")
            reason_ids.append(check_id)
            all_reason_ids.append(check_id)
            reasons.append(MappingReason(check_id, delta_kind.value, after_status))
        if reason_ids != sorted(set(reason_ids)):
            _mapping_fail("contract-order", "mapping reasons must be unique and sorted")
        matches.append(RunbookMatch(
            runbook_id,
            _mapping_string(match["title"], f"matches[{match_index}].title"),
            _mapping_path(match["path"]),
            _mapping_string(match["section"], f"matches[{match_index}].section"),
            tuple(reasons),
        ))
    if match_ids != sorted(set(match_ids)):
        _mapping_fail("contract-order", "runbook matches must be unique and sorted")

    unmapped_value = document["unmappedDeltaIds"]
    if not isinstance(unmapped_value, list) or not all(isinstance(item, str) and item for item in unmapped_value):
        _mapping_fail("contract-type", "unmappedDeltaIds must be a string array")
    unmapped = tuple(unmapped_value)
    if unmapped != tuple(sorted(set(unmapped))):
        _mapping_fail("contract-order", "unmappedDeltaIds must be unique and sorted")
    mapped_ids = set(all_reason_ids)
    if mapped_ids & set(unmapped):
        _mapping_fail("inconsistent-summary", "mapped and unmapped delta identifiers overlap")

    summary = _mapping_object(document["summary"], _SUMMARY_FIELDS, "summary")
    counts = {field: _mapping_count(summary[field], field) for field in _SUMMARY_FIELDS}
    expected_exit = 1 if unmapped else 0
    if counts["mappingExit"] not in (0, 1) or counts["mappingExit"] != expected_exit:
        _mapping_fail("inconsistent-summary", "mappingExit does not match unmapped deltas")
    expected = {
        "mappedDeltas": len(mapped_ids),
        "unmappedDeltas": len(unmapped),
        "runbookMatches": len(matches),
        "totalDeltas": len(mapped_ids | set(unmapped)),
    }
    if any(counts[field] != value for field, value in expected.items()):
        _mapping_fail("inconsistent-summary", "mapping summary counts do not match its contents")
    if document["limitations"] != [RUNBOOK_MAPPING_LIMITATION]:
        _mapping_fail("contract-value", "runbook mapping limitations do not match")

    return RunbookMapping(before_time, after_time, counts["totalDeltas"], tuple(matches), unmapped)


def load_runbook_mapping(path_text: str) -> RunbookMapping:
    """Read and validate one explicitly selected regular mapping file."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _mapping_fail("input-unavailable", "runbook mapping is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(RUNBOOK_MAPPING_INPUT_LIMIT + 1)
    except RunbookMappingError:
        raise
    except OSError:
        _mapping_fail("input-unavailable", "runbook mapping is not an accessible regular file")
    return parse_runbook_mapping_json(raw)


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
