"""Deterministic terminal and Markdown renderers."""

from __future__ import annotations

from collections import Counter
from typing import TextIO

from .models import CheckResult, EvaluatedSnapshot, Status


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
    stream.write("Scope: fixed SignalForge nodes, workloads, routing, Metrics APIService, and explicitly configured HTTP endpoints\n")
    stream.write("Redaction: credentials, kubeconfig paths, addresses, headers, and complete objects omitted\n\n")
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
    stream.write("- Scope: fixed SignalForge nodes, workloads, routing, Metrics APIService, and explicitly configured HTTP endpoints\n")
    stream.write("- Redaction: credentials, kubeconfig paths, addresses, headers, and complete objects omitted\n\n")
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
    stream.write("\nThis is a bounded point-in-time observation, not continuous monitoring, a compliance assessment, or a complete statement of cluster health.\n")
