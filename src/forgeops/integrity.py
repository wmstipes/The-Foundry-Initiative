"""Deterministic exact-byte integrity records for validated ForgeOps evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, TextIO

from .constants import EXPECTED_CONTEXT, SCHEMA_VERSION
from .evidence import (
    EVIDENCE_INPUT_LIMIT,
    EvidenceArtifact,
    EvidenceValidationError,
    load_evidence_artifact,
)


INTEGRITY_SCHEMA = "forgeops.integrity/v1alpha1"
INTEGRITY_ALGORITHM = "sha256"
INTEGRITY_RECORD_LIMIT = 64 * 1024
INTEGRITY_LIMITATION = (
    "This SHA-256 record detects exact byte differences only when compared "
    "with a separately retained trusted record; it does not establish "
    "authorship, authenticity, or chain of custody."
)
INTEGRITY_FIELDS = (
    "schema",
    "evidenceSchema",
    "collectedAtUtc",
    "context",
    "algorithm",
    "digest",
    "byteLength",
    "limitations",
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class IntegrityRecordError(ValueError):
    """A bounded, non-sensitive integrity-record failure."""

    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


@dataclass(frozen=True, slots=True)
class IntegrityRecord:
    schema: str
    evidence_schema: str
    collected_at_utc: str
    context: str
    algorithm: str
    digest: str
    byte_length: int
    limitations: tuple[str, ...] = (INTEGRITY_LIMITATION,)


@dataclass(frozen=True, slots=True)
class IntegrityVerification:
    matches: bool
    byte_length_matches: bool
    digest_matches: bool
    metadata_matches: bool

    @property
    def exit_code(self) -> int:
        return 0 if self.matches else 1


def _fail(code: str, summary: str) -> None:
    raise IntegrityRecordError(code, summary)


def create_integrity_record(artifact: EvidenceArtifact) -> IntegrityRecord:
    """Describe the exact bytes of one already validated evidence artifact."""

    snapshot = artifact.evidence.snapshot
    return IntegrityRecord(
        schema=INTEGRITY_SCHEMA,
        evidence_schema=snapshot.schema,
        collected_at_utc=snapshot.collected_at_utc,
        context=snapshot.context,
        algorithm=INTEGRITY_ALGORITHM,
        digest=sha256(artifact.raw).hexdigest(),
        byte_length=len(artifact.raw),
    )


def _record_value(record: IntegrityRecord) -> dict[str, object]:
    return {
        "schema": record.schema,
        "evidenceSchema": record.evidence_schema,
        "collectedAtUtc": record.collected_at_utc,
        "context": record.context,
        "algorithm": record.algorithm,
        "digest": record.digest,
        "byteLength": record.byte_length,
        "limitations": list(record.limitations),
    }


def render_integrity_record(record: IntegrityRecord, stream: TextIO) -> None:
    """Render one deterministic, disclosure-minimized integrity record."""

    json.dump(_record_value(record), stream, ensure_ascii=True, indent=2)
    stream.write("\n")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail("duplicate-key", "integrity record objects must not contain duplicate keys")
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    _fail("malformed-json", "integrity record must use standard JSON values")


def parse_integrity_record(raw: bytes) -> IntegrityRecord:
    """Strictly parse one forgeops.integrity/v1alpha1 record."""

    if len(raw) > INTEGRITY_RECORD_LIMIT:
        _fail("oversized-record", "integrity record exceeds the 64 KiB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("invalid-utf8", "integrity record must be UTF-8")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except IntegrityRecordError:
        raise
    except (json.JSONDecodeError, RecursionError):
        _fail("malformed-json", "integrity record must be one bounded JSON document")
    if not isinstance(value, dict) or tuple(value) != INTEGRITY_FIELDS:
        _fail("contract-fields", "integrity record fields or order are unsupported")
    for field in (
        "schema", "evidenceSchema", "collectedAtUtc", "context",
        "algorithm", "digest",
    ):
        if not isinstance(value[field], str) or not value[field]:
            _fail("contract-type", f"{field} must be a non-empty string")
    if value["schema"] != INTEGRITY_SCHEMA:
        _fail("unsupported-schema", "integrity record schema is not supported")
    if value["evidenceSchema"] != SCHEMA_VERSION:
        _fail("unsupported-evidence-schema", "evidence schema is not supported")
    if value["context"] != EXPECTED_CONTEXT:
        _fail("contract-value", "context does not match the supported contract")
    try:
        datetime.strptime(value["collectedAtUtc"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        _fail("contract-timestamp", "collectedAtUtc must use RFC 3339 UTC seconds")
    if value["algorithm"] != INTEGRITY_ALGORITHM:
        _fail("unsupported-algorithm", "integrity algorithm is not supported")
    if _SHA256_PATTERN.fullmatch(value["digest"]) is None:
        _fail("contract-digest", "digest must be a lowercase SHA-256 value")
    if (
        type(value["byteLength"]) is not int
        or not 0 < value["byteLength"] <= EVIDENCE_INPUT_LIMIT
    ):
        _fail("contract-length", "byteLength must fit the evidence input boundary")
    if value["limitations"] != [INTEGRITY_LIMITATION]:
        _fail("contract-value", "integrity limitations do not match the contract")
    return IntegrityRecord(
        schema=value["schema"],
        evidence_schema=value["evidenceSchema"],
        collected_at_utc=value["collectedAtUtc"],
        context=value["context"],
        algorithm=value["algorithm"],
        digest=value["digest"],
        byte_length=value["byteLength"],
    )


def load_integrity_record(path_text: str) -> IntegrityRecord:
    """Read exactly one selected regular integrity-record file."""

    try:
        path = Path(path_text).expanduser().resolve(strict=True)
        if not path.is_file():
            _fail("record-unavailable", "integrity record is not an accessible regular file")
        with path.open("rb") as stream:
            raw = stream.read(INTEGRITY_RECORD_LIMIT + 1)
    except IntegrityRecordError:
        raise
    except OSError:
        _fail("record-unavailable", "integrity record is not an accessible regular file")
    return parse_integrity_record(raw)


def load_integrity_inputs(
    evidence_path: str,
    record_path: str,
) -> tuple[EvidenceArtifact, IntegrityRecord]:
    """Load a validated evidence artifact and its strict integrity record."""

    artifact = load_evidence_artifact(evidence_path)
    record = load_integrity_record(record_path)
    return artifact, record


def verify_integrity(
    artifact: EvidenceArtifact,
    record: IntegrityRecord,
) -> IntegrityVerification:
    """Compare validated evidence bytes and metadata with a trusted record."""

    actual = create_integrity_record(artifact)
    length_matches = actual.byte_length == record.byte_length
    digest_matches = actual.digest == record.digest
    metadata_matches = (
        actual.evidence_schema == record.evidence_schema
        and actual.collected_at_utc == record.collected_at_utc
        and actual.context == record.context
    )
    return IntegrityVerification(
        matches=length_matches and digest_matches and metadata_matches,
        byte_length_matches=length_matches,
        digest_matches=digest_matches,
        metadata_matches=metadata_matches,
    )


def render_integrity_verification(
    verification: IntegrityVerification,
    stream: TextIO,
) -> None:
    """Render a bounded result without paths or evidence contents."""

    status = "MATCH" if verification.matches else "MISMATCH"
    stream.write(
        f"{status} {INTEGRITY_SCHEMA} "
        f"length={'match' if verification.byte_length_matches else 'mismatch'} "
        f"digest={'match' if verification.digest_matches else 'mismatch'} "
        f"metadata={'match' if verification.metadata_matches else 'mismatch'}\n"
    )
