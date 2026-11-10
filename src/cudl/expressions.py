"""Safe parser for the first CUDL value-expression subset.

CUDL values are dynamically typed. Unquoted values are ordinary text unless
they are a number, boolean, null, or a hash-prefixed variable path. Indexing
is limited to safe mapping and sequence access; source is never executed.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import math
import re


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PATH_ROOT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")


class ExpressionError(ValueError):
    """Raised when source is outside the supported safe expression grammar."""


@dataclass(frozen=True, slots=True)
class Expression:
    kind: str
    value: object
    path: tuple[str | int, ...] = ()

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"kind": self.kind, "value": self.value}
        if self.path:
            result["path"] = list(self.path)
        return result


def _parse_path(raw: str) -> tuple[str | int, ...]:
    """Parse #name.path[index] without allowing calls or arbitrary code."""
    source = raw[1:] if raw.startswith("#") else raw
    match = _PATH_ROOT.match(source)
    if not match:
        raise ExpressionError("A variable path must start with a valid name.")

    parts: list[str | int] = [match.group(0)]
    index = match.end()
    while index < len(source):
        if source[index] == ".":
            segment = _PATH_ROOT.match(source, index + 1)
            if not segment:
                raise ExpressionError("Expected a property name after '.'.")
            parts.append(segment.group(0))
            index = segment.end()
            continue

        if source[index] == "[":
            end = source.find("]", index + 1)
            if end < 0:
                raise ExpressionError("Index is missing its closing ']'.")
            raw_key = source[index + 1:end].strip()
            if not raw_key:
                raise ExpressionError("An index cannot be empty.")
            if re.fullmatch(r"0|[1-9]\d*", raw_key):
                parts.append(int(raw_key))
            elif _IDENTIFIER.fullmatch(raw_key):
                parts.append(raw_key)
            elif raw_key.startswith(("'", '"')):
                try:
                    key = ast.literal_eval(raw_key)
                except (SyntaxError, ValueError) as exc:
                    raise ExpressionError("Invalid quoted index key.") from exc
                if not isinstance(key, str):
                    raise ExpressionError("Index keys must be strings or non-negative integers.")
                parts.append(key)
            else:
                raise ExpressionError("Indexes must be names, strings, or non-negative integers.")
            index = end + 1
            continue

        raise ExpressionError("Expected '.', '[' or the end of a variable path.")

    return tuple(parts)


def parse_expression(source: str) -> Expression:
    """Parse a dynamic value or safe hash-prefixed data path without executing code."""
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

    if raw.startswith("#"):
        return Expression("path", raw, _parse_path(raw))

    # Plain text stays text, even when it contains dots, brackets, or
    # parentheses. Only the explicit hash marker requests variable lookup.
    return Expression("string", raw)


def resolve_path(expression: Expression, data: object) -> object:
    """Resolve a parsed data path through mappings and indexed sequences."""
    if expression.kind != "path":
        return expression.value

    current = data
    for part in expression.path:
        if isinstance(part, int):
            if not isinstance(current, (list, tuple)) or part >= len(current):
                raise KeyError(part)
            current = current[part]
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(part)
            current = current[part]
        else:
            raise KeyError(part)
    return current
