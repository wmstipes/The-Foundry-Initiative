"""Exact offline replay for deterministic ForgeOps incident briefs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from .incident import IncidentBrief


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
