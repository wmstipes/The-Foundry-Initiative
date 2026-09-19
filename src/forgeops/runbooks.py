"""Strict offline contracts for grounded ForgeOps runbook knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Any

from .comparison import DeltaKind
from .models import Status


RUNBOOK_CATALOG_SCHEMA = "forgeops.runbook-catalog/v1alpha1"
RUNBOOK_CATALOG_INPUT_LIMIT = 256 * 1024
RUNBOOK_CATALOG_LIMITATION = (
    "This catalog identifies repository runbook sections and bounded signal "
    "selectors; it does not establish applicability, causation, diagnosis, "
    "recommendation, or remediation authority."
)


class RunbookCatalogError(ValueError):
    """A bounded, non-sensitive runbook-catalog validation failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


@dataclass(frozen=True, slots=True)
class RunbookSignal:
    match: str
    check_id: str
    delta_kinds: tuple[DeltaKind, ...]
    after_statuses: tuple[Status, ...]


@dataclass(frozen=True, slots=True)
class RunbookEntry:
    runbook_id: str
    title: str
    path: str
    section: str
    signals: tuple[RunbookSignal, ...]


@dataclass(frozen=True, slots=True)
class RunbookCatalog:
    entries: tuple[RunbookEntry, ...]


_TOP_LEVEL_FIELDS = ("schema", "entries", "limitations")
_ENTRY_FIELDS = ("id", "title", "path", "section", "signals")
_SIGNAL_FIELDS = ("match", "checkId", "deltaKinds", "afterStatuses")
_MATCH_VALUES = ("exact", "prefix")
_DELTA_ORDER = tuple(DeltaKind)
_STATUS_ORDER = tuple(Status)


def _fail(code: str, summary: str) -> None:
    raise RunbookCatalogError(code, summary)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail("duplicate-key", "catalog objects must not contain duplicate keys")
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    _fail("malformed-json", "catalog must use standard JSON values")


def _object(value: Any, fields: tuple[str, ...], scope: str) -> dict[str, Any]:
    if not isinstance(value, dict) or tuple(value) != fields:
        _fail("contract-fields", f"{scope} fields or field order are unsupported")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _fail("contract-type", f"{field} must be a non-empty string")
    return value


def _ordered_enum_array(
    value: Any,
    enum_type: type[DeltaKind] | type[Status],
    allowed: tuple[DeltaKind, ...] | tuple[Status, ...],
    field: str,
) -> tuple[Any, ...]:
    if not isinstance(value, list) or not value:
        _fail("contract-type", f"{field} must be a non-empty array")
    try:
        parsed = tuple(enum_type(_string(item, field)) for item in value)
    except ValueError:
        _fail("contract-value", f"{field} contains an unsupported value")
    expected = tuple(item for item in allowed if item in parsed)
    if len(set(parsed)) != len(parsed) or parsed != expected:
        _fail("contract-order", f"{field} must be unique and canonically ordered")
    return parsed


def _validate_path(value: Any) -> str:
    path = _string(value, "entry.path")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or ".." in parsed.parts
        or parsed.suffix != ".md"
        or parsed.parts[:2] != ("docs", "runbooks")
    ):
        _fail("contract-path", "runbook path must be a repository-relative Markdown path under docs/runbooks")
    return path


def parse_runbook_catalog_json(raw: bytes) -> RunbookCatalog:
    """Parse one bounded, deterministic runbook catalog."""

    if len(raw) > RUNBOOK_CATALOG_INPUT_LIMIT:
        _fail("oversized-input", "runbook catalog exceeds the 256 KiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("invalid-utf8", "runbook catalog must be UTF-8")
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except RunbookCatalogError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _fail("malformed-json", "runbook catalog must be one bounded JSON document")

    document = _object(decoded, _TOP_LEVEL_FIELDS, "top-level")
    if document["schema"] != RUNBOOK_CATALOG_SCHEMA:
        _fail("unsupported-schema", "runbook catalog schema is not supported")
    if document["limitations"] != [RUNBOOK_CATALOG_LIMITATION]:
        _fail("contract-value", "runbook catalog limitations do not match")
    raw_entries = document["entries"]
    if not isinstance(raw_entries, list) or not raw_entries:
        _fail("contract-type", "entries must be a non-empty array")

    entries: list[RunbookEntry] = []
    entry_ids: list[str] = []
    for entry_index, raw_entry in enumerate(raw_entries):
        entry = _object(raw_entry, _ENTRY_FIELDS, f"entries[{entry_index}]")
        runbook_id = _string(entry["id"], f"entries[{entry_index}].id")
        entry_ids.append(runbook_id)
        raw_signals = entry["signals"]
        if not isinstance(raw_signals, list) or not raw_signals:
            _fail("contract-type", "signals must be a non-empty array")
        signals: list[RunbookSignal] = []
        signal_keys: list[tuple[str, str]] = []
        for signal_index, raw_signal in enumerate(raw_signals):
            signal = _object(
                raw_signal,
                _SIGNAL_FIELDS,
                f"entries[{entry_index}].signals[{signal_index}]",
            )
            match = _string(signal["match"], "signal.match")
            if match not in _MATCH_VALUES:
                _fail("contract-value", "signal.match is not supported")
            check_id = _string(signal["checkId"], "signal.checkId")
            if match == "prefix" and not check_id.endswith("."):
                _fail("contract-value", "prefix selectors must end with a dot")
            kinds = _ordered_enum_array(
                signal["deltaKinds"], DeltaKind, _DELTA_ORDER, "signal.deltaKinds",
            )
            statuses = _ordered_enum_array(
                signal["afterStatuses"], Status, _STATUS_ORDER, "signal.afterStatuses",
            )
            signal_keys.append((match, check_id))
            signals.append(RunbookSignal(match, check_id, kinds, statuses))
        if signal_keys != sorted(set(signal_keys)):
            _fail("contract-order", "signals must be unique and sorted by match and checkId")
        entries.append(RunbookEntry(
            runbook_id=runbook_id,
            title=_string(entry["title"], f"entries[{entry_index}].title"),
            path=_validate_path(entry["path"]),
            section=_string(entry["section"], f"entries[{entry_index}].section"),
            signals=tuple(signals),
        ))
    if entry_ids != sorted(set(entry_ids)):
        _fail("contract-order", "entry identifiers must be unique and sorted")
    return RunbookCatalog(tuple(entries))


def load_runbook_catalog(path_text: str) -> RunbookCatalog:
    """Read and validate one explicitly selected regular catalog file."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _fail("input-unavailable", "runbook catalog is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(RUNBOOK_CATALOG_INPUT_LIMIT + 1)
    except RunbookCatalogError:
        raise
    except OSError:
        _fail("input-unavailable", "runbook catalog is not an accessible regular file")
    return parse_runbook_catalog_json(raw)
