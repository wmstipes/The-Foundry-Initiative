"""Deterministic terminal, Markdown, and JSON renderers."""

from __future__ import annotations

from collections import Counter
import json
from typing import TextIO

from .models import CheckResult, EvaluatedSnapshot, Status


SCOPE_DESCRIPTION = (
    "fixed SignalForge nodes, workloads, routing, Metrics APIService, "
    "and explicitly configured HTTP endpoints"
)
REDACTION_DESCRIPTION = (
    "credentials, kubeconfig paths, addresses, headers, and complete objects omitted"
)
LIMITATION_DESCRIPTION = (
    "This is a bounded point-in-time observation, not continuous monitoring, "
    "a compliance assessment, or a complete statement of cluster health."
)


def _summary(snapshot: EvaluatedSnapshot) -> Counter[Status]:
    return Counter(check.status for check in snapshot.checks)


def _detail(check: CheckResult) -> str:
    details: list[str] = []
    if check.expected is not None:
        details.append(f"expected: {check.expected}")
    if check.observed is not None:
        details.append(f"observed: {check.observed}")
    if check.error_category is not None:
        details.append(f"error: {check.error_category}")
    return "; ".join(details)


def render_text(snapshot: EvaluatedSnapshot, stream: TextIO) -> None:
    stream.write("ForgeOps SignalForge snapshot\n")
    stream.write(f"Schema: {snapshot.schema}\n")
    stream.write(f"Collected: {snapshot.collected_at_utc}\n")
    stream.write(f"Context: {snapshot.context}\n")
    stream.write(f"Scope: {SCOPE_DESCRIPTION}\n")
    stream.write(f"Redaction: {REDACTION_DESCRIPTION}\n\n")
    for check in snapshot.checks:
        stream.write(f"{check.status.value:<7} {check.check_id}\n")
        stream.write(f"        {check.observation}\n")
        stream.write(f"        source: {check.source}\n")
        detail = _detail(check)
        if detail:
            stream.write(f"        {detail}\n")
    counts = _summary(snapshot)
    stream.write(
        "\nSummary: "
        f"{counts[Status.PASS]} PASS, {counts[Status.WARN]} WARN, "
        f"{counts[Status.FAIL]} FAIL, {counts[Status.UNKNOWN]} UNKNOWN; "
        f"overall={snapshot.overall_status.value}; exit={snapshot.exit_code}\n"
    )


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(snapshot: EvaluatedSnapshot, stream: TextIO) -> None:
    stream.write("# ForgeOps SignalForge snapshot\n\n")
    stream.write(f"- Schema: `{snapshot.schema}`\n")
    stream.write(f"- Collected: `{snapshot.collected_at_utc}`\n")
    stream.write(f"- Context: `{snapshot.context}`\n")
    stream.write(f"- Scope: {SCOPE_DESCRIPTION}\n")
    stream.write(f"- Redaction: {REDACTION_DESCRIPTION}\n\n")
    stream.write("| Status | Check | Observation | Evidence |\n")
    stream.write("| --- | --- | --- | --- |\n")
    for check in snapshot.checks:
        detail = _detail(check)
        evidence = f"{check.source}; {detail}" if detail else check.source
        stream.write(
            f"| {check.status.value} | `{_escape(check.check_id)}` | "
            f"{_escape(check.observation)} | {_escape(evidence)} |\n"
        )
    counts = _summary(snapshot)
    stream.write("\n## Summary\n\n")
    stream.write(
        f"{counts[Status.PASS]} PASS, {counts[Status.WARN]} WARN, "
        f"{counts[Status.FAIL]} FAIL, and {counts[Status.UNKNOWN]} UNKNOWN. "
        f"Overall: **{snapshot.overall_status.value}**. Exit code: `{snapshot.exit_code}`.\n"
    )
    stream.write(f"\n{LIMITATION_DESCRIPTION}\n")


def _json_check(check: CheckResult) -> dict[str, str]:
    value = {
        "id": check.check_id,
        "status": check.status.value,
        "observation": check.observation,
        "source": check.source,
        "collectedAtUtc": check.collected_at_utc,
    }
    if check.expected is not None:
        value["expected"] = check.expected
    if check.observed is not None:
        value["observed"] = check.observed
    if check.error_category is not None:
        value["errorCategory"] = check.error_category
    return value


def render_json(snapshot: EvaluatedSnapshot, stream: TextIO) -> None:
    """Render the evaluated, redacted snapshot as deterministic JSON."""

    counts = _summary(snapshot)
    value = {
        "schema": snapshot.schema,
        "collectedAtUtc": snapshot.collected_at_utc,
        "context": snapshot.context,
        "scope": SCOPE_DESCRIPTION,
        "redaction": REDACTION_DESCRIPTION,
        "summary": {
            "pass": counts[Status.PASS],
            "warn": counts[Status.WARN],
            "fail": counts[Status.FAIL],
            "unknown": counts[Status.UNKNOWN],
            "overallStatus": snapshot.overall_status.value,
            "exitCode": snapshot.exit_code,
        },
        "checks": [_json_check(check) for check in snapshot.checks],
        "limitations": [LIMITATION_DESCRIPTION],
    }
    json.dump(value, stream, ensure_ascii=True, indent=2)
    stream.write("\n")
