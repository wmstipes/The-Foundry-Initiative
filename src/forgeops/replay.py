"""Bounded offline replay against an explicit expected comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from .comparison import EvidenceComparison


REPLAY_SCHEMA = "forgeops.scenario-replay/v1alpha1"


@dataclass(frozen=True, slots=True)
class ScenarioReplay:
    expected: EvidenceComparison
    actual: EvidenceComparison

    @property
    def matches(self) -> bool:
        return self.actual == self.expected

    @property
    def exit_code(self) -> int:
        return 0 if self.matches else 1


def replay_scenario(
    actual: EvidenceComparison,
    expected: EvidenceComparison,
) -> ScenarioReplay:
    """Compare an actual deterministic result with one validated expectation."""

    return ScenarioReplay(expected=expected, actual=actual)


def render_scenario_replay(replay: ScenarioReplay, stream: TextIO) -> None:
    """Render a disclosure-minimized replay result."""

    status = "MATCH" if replay.matches else "MISMATCH"
    stream.write(
        f"{status} {REPLAY_SCHEMA} "
        f"expectedComparisonExit={replay.expected.exit_code} "
        f"actualComparisonExit={replay.actual.exit_code} "
        f"expectedDeltas={len(replay.expected.deltas)} "
        f"actualDeltas={len(replay.actual.deltas)}\n"
    )
