"""Structured result models used by repository checks and renderers."""

from dataclasses import dataclass, field
from typing import Literal

CheckStatus = Literal["pass", "warning", "fail"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    """The stable, presentation-independent result of one repository check."""

    check_id: str
    display_name: str
    status: CheckStatus
    message: str
    details: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of this result."""

        return {
            "id": self.check_id,
            "name": self.display_name,
            "status": self.status,
            "message": self.message,
            "details": list(self.details),
        }
