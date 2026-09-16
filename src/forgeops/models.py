"""Presentation-independent ForgeOps evidence and evaluation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CollectionError:
    category: str
    summary: str


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    source: str
    value: Any = None
    error: CollectionError | None = None


@dataclass(frozen=True, slots=True)
class RawSnapshot:
    schema: str
    collected_at_utc: str
    context: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True, slots=True)
class CheckResult:
    check_id: str
    status: Status
    observation: str
    source: str
    collected_at_utc: str
    expected: str | None = None
    observed: str | None = None
    error_category: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluatedSnapshot:
    schema: str
    collected_at_utc: str
    context: str
    checks: tuple[CheckResult, ...] = field(default_factory=tuple)

    @property
    def exit_code(self) -> int:
        if any(check.status is Status.UNKNOWN for check in self.checks):
            return 2
        if any(check.status in (Status.WARN, Status.FAIL) for check in self.checks):
            return 1
        return 0

    @property
    def overall_status(self) -> Status:
        if any(check.status is Status.UNKNOWN for check in self.checks):
            return Status.UNKNOWN
        if any(check.status is Status.FAIL for check in self.checks):
            return Status.FAIL
        if any(check.status is Status.WARN for check in self.checks):
            return Status.WARN
        return Status.PASS


def utc_now() -> str:
    """Return a stable RFC 3339 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
