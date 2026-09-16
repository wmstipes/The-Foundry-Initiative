"""Strict offline loading for ForgeOps evaluated evidence artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .constants import (
    EXPECTED_CONTEXT,
    LIMITATION_DESCRIPTION,
    REDACTION_DESCRIPTION,
    SCHEMA_VERSION,
    SCOPE_DESCRIPTION,
)
from .models import CheckResult, EvaluatedSnapshot, Status


EVIDENCE_INPUT_LIMIT = 1024 * 1024
TOP_LEVEL_FIELDS = (
    "schema",
    "collectedAtUtc",
    "context",
    "scope",
    "redaction",
    "summary",
    "checks",
    "limitations",
)
SUMMARY_FIELDS = ("pass", "warn", "fail", "unknown", "overallStatus", "exitCode")
CHECK_FIELDS = ("id", "status", "observation", "source", "collectedAtUtc")
OPTIONAL_CHECK_FIELDS = ("expected", "observed", "errorCategory")


class EvidenceValidationError(ValueError):
    """A bounded, non-sensitive evidence validation failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


@dataclass(frozen=True, slots=True)
class ValidatedEvidence:
    """A contract-validated evaluated snapshot and its disclosure statements."""

    snapshot: EvaluatedSnapshot
    scope: str
    redaction: str
    limitations: tuple[str, ...]


def _fail(code: str, summary: str) -> None:
    raise EvidenceValidationError(code, summary)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail("duplicate-key", "JSON objects must not contain duplicate keys")
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    _fail("malformed-json", "JSON must not contain non-standard numeric constants")


def _require_object(value: Any, code: str, summary: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(code, summary)
    return value


def _require_exact_fields(value: dict[str, Any], expected: tuple[str, ...], scope: str) -> None:
    if tuple(value) != expected:
        _fail("contract-fields", f"{scope} fields or field order do not match the supported contract")


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _fail("contract-type", f"{field} must be a non-empty string")
    return value


def _require_timestamp(value: Any, field: str) -> str:
    timestamp = _require_nonempty_string(value, field)
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        _fail("contract-timestamp", f"{field} must be an RFC 3339 UTC timestamp with second precision")
    return timestamp


def _require_count(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        _fail("contract-type", f"summary.{field} must be a non-negative integer")
    return value


def parse_evidence_json(raw: bytes) -> ValidatedEvidence:
    """Parse and validate one bounded forgeops.snapshot/v1alpha1 artifact."""

    if len(raw) > EVIDENCE_INPUT_LIMIT:
        _fail("oversized-input", "evidence input exceeds the 1 MiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("invalid-utf8", "evidence input must be UTF-8")
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except EvidenceValidationError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _fail("malformed-json", "evidence input must be one bounded JSON document")

    document = _require_object(
        decoded, "contract-type", "evidence document must be a JSON object",
    )
    _require_exact_fields(document, TOP_LEVEL_FIELDS, "top-level")

    schema = _require_nonempty_string(document["schema"], "schema")
    if schema != SCHEMA_VERSION:
        _fail("unsupported-schema", "evidence schema is not supported")
    collected_at = _require_timestamp(document["collectedAtUtc"], "collectedAtUtc")
    context = _require_nonempty_string(document["context"], "context")
    if context != EXPECTED_CONTEXT:
        _fail("contract-value", "context does not match the supported SignalForge contract")
    if document["scope"] != SCOPE_DESCRIPTION:
        _fail("contract-value", "scope does not match the supported contract")
    if document["redaction"] != REDACTION_DESCRIPTION:
        _fail("contract-value", "redaction statement does not match the supported contract")
    if document["limitations"] != [LIMITATION_DESCRIPTION]:
        _fail("contract-value", "limitations do not match the supported contract")

    checks_value = document["checks"]
    if not isinstance(checks_value, list) or not checks_value:
        _fail("contract-type", "checks must be a non-empty array")
    checks: list[CheckResult] = []
    identifiers: set[str] = set()
    for index, raw_check in enumerate(checks_value):
        check = _require_object(
            raw_check, "contract-type", "each check must be a JSON object",
        )
        optional = tuple(field for field in OPTIONAL_CHECK_FIELDS if field in check)
        _require_exact_fields(check, CHECK_FIELDS + optional, f"checks[{index}]")
        check_id = _require_nonempty_string(check["id"], f"checks[{index}].id")
        if check_id in identifiers:
            _fail("duplicate-check", "check identifiers must be unique")
        identifiers.add(check_id)
        try:
            status = Status(_require_nonempty_string(check["status"], f"checks[{index}].status"))
        except ValueError:
            _fail("contract-status", "check status is not supported")
        check_time = _require_timestamp(check["collectedAtUtc"], f"checks[{index}].collectedAtUtc")
        if check_time != collected_at:
            _fail("contract-timestamp", "check timestamps must match the artifact collection time")
        detail: dict[str, str | None] = {
            "expected": None,
            "observed": None,
            "errorCategory": None,
        }
        for field in optional:
            detail[field] = _require_nonempty_string(check[field], f"checks[{index}].{field}")
        checks.append(CheckResult(
            check_id=check_id,
            status=status,
            observation=_require_nonempty_string(
                check["observation"], f"checks[{index}].observation",
            ),
            source=_require_nonempty_string(check["source"], f"checks[{index}].source"),
            collected_at_utc=check_time,
            expected=detail["expected"],
            observed=detail["observed"],
            error_category=detail["errorCategory"],
        ))

    snapshot = EvaluatedSnapshot(schema, collected_at, context, tuple(checks))
    summary = _require_object(
        document["summary"], "contract-type", "summary must be a JSON object",
    )
    _require_exact_fields(summary, SUMMARY_FIELDS, "summary")
    expected_counts = {
        "pass": sum(check.status is Status.PASS for check in checks),
        "warn": sum(check.status is Status.WARN for check in checks),
        "fail": sum(check.status is Status.FAIL for check in checks),
        "unknown": sum(check.status is Status.UNKNOWN for check in checks),
    }
    for field, expected in expected_counts.items():
        if _require_count(summary[field], field) != expected:
            _fail("inconsistent-summary", "summary counts do not match the checks")
    if summary["overallStatus"] != snapshot.overall_status.value:
        _fail("inconsistent-summary", "summary overall status does not match the checks")
    if type(summary["exitCode"]) is not int or summary["exitCode"] != snapshot.exit_code:
        _fail("inconsistent-summary", "summary exit code does not match the checks")

    return ValidatedEvidence(
        snapshot=snapshot,
        scope=SCOPE_DESCRIPTION,
        redaction=REDACTION_DESCRIPTION,
        limitations=(LIMITATION_DESCRIPTION,),
    )


def load_evidence_file(path_text: str) -> ValidatedEvidence:
    """Read exactly one operator-selected regular file and validate its contract."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _fail("input-unavailable", "evidence input is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(EVIDENCE_INPUT_LIMIT + 1)
    except EvidenceValidationError:
        raise
    except OSError:
        _fail("input-unavailable", "evidence input is not an accessible regular file")
    return parse_evidence_json(raw)
