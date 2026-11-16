"""Structured, source-aware diagnostics emitted by the CUDL front end."""

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
    end_column: int | None = None
    line_text: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-friendly diagnostic with source context."""
        result = asdict(self)
        result["severity"] = self.severity.value
        return result

    def format(self) -> str:
        """Render a compact compiler-style diagnostic and optional source caret."""
        location = f"{self.source}:" if self.source else ""
        output = [f"{location}{self.line}:{self.column}: {self.severity.value} {self.code}: {self.message}"]
        if self.line_text is not None:
            output.append(f"  {self.line_text}")
            width = max(1, (self.end_column or self.column + 1) - self.column)
            output.append("  " + " " * max(0, self.column - 1) + "^" * width)
        if self.suggestion:
            output.append(f"  help: {self.suggestion}")
        return "\n".join(output)
