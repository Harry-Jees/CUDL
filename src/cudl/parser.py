"""A small, framework-neutral parser for the first CUDL syntax subset.

This parser intentionally builds a generic tree. Meaning and rendering belong
to later semantic passes and host adapters, not to the parser itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .diagnostics import Diagnostic, Severity


@dataclass(slots=True)
class Node:
    kind: str
    value: str = ""
    children: list["Node"] = field(default_factory=list)
    line: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "value": self.value,
            "line": self.line,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(slots=True)
class Document:
    nodes: list[Node]
    source: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLDocument",
            "version": 1,
            "source": self.source,
            "nodes": [node.to_dict() for node in self.nodes],
        }


@dataclass(slots=True)
class ParseResult:
    document: Document
    diagnostics: list[Diagnostic]

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self.diagnostics)


_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*")
_AT_NAME = re.compile(r"^@([A-Za-z_][A-Za-z0-9_-]*)")
_VARIABLE_ASSIGNMENT = re.compile(r"^#[A-Za-z_][A-Za-z0-9_]*\\s*=\\s*\\S.*$")


def _strip_comment(text: str) -> str:
    """Remove an inline double-hash comment without touching quoted text."""
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif text.startswith("##", index):
            return text[:index].rstrip()
        index += 1
    return text.strip()


def _split_statement(text: str) -> tuple[str, str]:
    """Split a statement while preserving CUDL's special prefixes."""
    if text.startswith("#"):
        return "variable", text
    if text.startswith("@"):
        match = _AT_NAME.match(text)
        if match:
            return "@" + match.group(1).casefold(), text[match.end():].strip()
        return text, ""
    match = _NAME.match(text)
    if not match:
        return text, ""
    return match.group(0).casefold(), text[match.end():].strip()


def parse(text: str, source: str | None = None) -> ParseResult:
    """Parse the supported indentation-based CUDL subset.

    Four spaces form one indentation level. Blank lines and full-line comments
    beginning with double hash are ignored. A single hash starts a variable
    declaration/reference and is never treated as a comment.
    """
    roots: list[Node] = []
    diagnostics: list[Diagnostic] = []
    stack: list[tuple[int, Node]] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("##"):
            continue

        leading = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in leading:
            diagnostics.append(Diagnostic(
                code="CUDL1001",
                message="Tabs are not allowed for indentation; use four spaces.",
                severity=Severity.ERROR,
                line=line_number,
                column=1,
                source=source,
                suggestion="Replace indentation tabs with spaces.",
            ))
            continue

        indent = len(leading)
        if indent % 4:
            diagnostics.append(Diagnostic(
                code="CUDL1002",
                message="Indentation must use multiples of four spaces.",
                severity=Severity.ERROR,
                line=line_number,
                column=1,
                source=source,
                suggestion="Align this statement to a four-space indentation level.",
            ))
            continue

        statement = _strip_comment(raw[indent:])
        if not statement:
            continue

        if statement.startswith("#") and not _VARIABLE_ASSIGNMENT.fullmatch(statement):
            diagnostics.append(Diagnostic(
                code="CUDL1004",
                message="A variable statement must assign a value to a valid hash-prefixed name.",
                severity=Severity.ERROR,
                line=line_number,
                column=indent + 1,
                source=source,
                suggestion="Use: #name = value",
            ))
            continue

        kind, value = _split_statement(statement)
        node = Node(kind=kind, value=value, line=line_number)

        while stack and stack[-1][0] >= indent:
            stack.pop()

        expected_indent = stack[-1][0] + 4 if stack else 0
        if indent > expected_indent:
            diagnostics.append(Diagnostic(
                code="CUDL1003",
                message="Unexpected indentation level.",
                severity=Severity.ERROR,
                line=line_number,
                column=indent + 1,
                source=source,
                suggestion="Indent nested statements by exactly four spaces.",
            ))
            indent = expected_indent

        if stack and indent == stack[-1][0] + 4:
            stack[-1][1].children.append(node)
        else:
            roots.append(node)

        stack.append((indent, node))

    return ParseResult(
        document=Document(nodes=roots, source=source),
        diagnostics=diagnostics,
    )
