"""Structured diagnostics emitted by the CUDL front end."""

from dataclasses import asdict, dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    severity: Severity
    line: int
    column: int = 1
    source: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["severity"] = self.severity.value
        return result
