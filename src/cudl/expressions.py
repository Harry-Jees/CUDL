"""Safe parser for the first CUDL value-expression subset.

Expressions are data, never executable source. This module deliberately supports
only literals and dotted data paths; calls, operators, indexing, and eval are
not part of this initial contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import math
import re


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PATH = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_NUMBER = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")


class ExpressionError(ValueError):
    """Raised when source is outside the supported safe expression grammar."""


@dataclass(frozen=True, slots=True)
class Expression:
    kind: str
    value: object
    path: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"kind": self.kind, "value": self.value}
        if self.path:
            result["path"] = list(self.path)
        return result


def parse_expression(source: str) -> Expression:
    """Parse a literal or dotted identifier path without executing code."""
    raw = source.strip()
    if not raw:
        raise ExpressionError("A value is required.")

    if raw[0] in ("'", '"'):
        try:
            value = ast.literal_eval(raw)
        except (SyntaxError, ValueError) as exc:
            raise ExpressionError("Invalid quoted string literal.") from exc
        if not isinstance(value, str):
            raise ExpressionError("Only string literals are supported here.")
        return Expression("string", value)

    lowered = raw.casefold()
    if lowered == "true":
        return Expression("boolean", True)
    if lowered == "false":
        return Expression("boolean", False)
    if lowered in {"null", "none"}:
        return Expression("null", None)

    if _NUMBER.fullmatch(raw):
        value = float(raw) if any(char in raw for char in ".eE") else int(raw)
        if isinstance(value, float) and not math.isfinite(value):
            raise ExpressionError("Numeric values must be finite.")
        return Expression("number", value)

    if _PATH.fullmatch(raw):
        parts = tuple(raw.split("."))
        return Expression("path", ".".join(parts), parts)

    raise ExpressionError(
        "Expected a string, number, boolean, null, or dotted data path; "
        "calls and operators are not supported."
    )


def resolve_path(expression: Expression, data: object) -> object:
    """Resolve a parsed data path from mappings/objects without evaluating code."""
    if expression.kind != "path":
        return expression.value
    current = data
    for part in expression.path:
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(part)
            current = current[part]
        else:
            raise KeyError(part)
    return current
