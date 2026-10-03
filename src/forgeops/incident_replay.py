"""Exact offline replay for deterministic ForgeOps incident briefs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from .incident import IncidentBrief
from .incident_context import SnapshotIncidentBrief


INCIDENT_REPLAY_SCHEMA = "forgeops.incident-replay/v1alpha1"


@dataclass(frozen=True, slots=True)
class IncidentReplay:
    actual: IncidentBrief
    expected: IncidentBrief

    @property
    def matches(self) -> bool:
        return self.actual == self.expected

    @property
    def exit_code(self) -> int:
        return 0 if self.matches else 1


def replay_incident_brief(actual: IncidentBrief, expected: IncidentBrief) -> IncidentReplay:
    return IncidentReplay(actual, expected)


def render_incident_replay(replay: IncidentReplay, stream: TextIO) -> None:
    status = "MATCH" if replay.matches else "MISMATCH"
    stream.write(
        f"{status} {INCIDENT_REPLAY_SCHEMA} "
        f"expectedState={replay.expected.state.value} "
        f"actualState={replay.actual.state.value}\n"
    )


def replay_snapshot_brief(
    actual: SnapshotIncidentBrief, expected: SnapshotIncidentBrief, stream: TextIO,
) -> int:
    """Compare complete v1alpha2 context, not merely its delta state."""
    matches = actual == expected
    stream.write(
        f"{'MATCH' if matches else 'MISMATCH'} forgeops.incident-replay/v1alpha2 "
        f"expectedOverall={expected.after.overall_status.value} "
        f"actualOverall={actual.after.overall_status.value} "
        f"expectedRecovery={expected.assessment['recovery']} "
        f"actualRecovery={actual.assessment['recovery']}\n"
    )
    return 0 if matches else 1
