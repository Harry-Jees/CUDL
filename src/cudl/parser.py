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


def _split_statement(text: str) -> tuple[str, str]:
    """Split a statement into its leading identifier and remaining payload."""
    match = _NAME.match(text)
    if not match:
        return text, ""
    return match.group(0).lower(), text[match.end():].strip()


def parse(text: str, source: str | None = None) -> ParseResult:
    """Parse the supported indentation-based CUDL subset.

    Four spaces form one indentation level. Blank lines and full-line comments
    are ignored. The parser preserves unknown statement names as generic nodes
    so future language features can be added without coupling parsing to UI
    semantics.
    """
    roots: list[Node] = []
    diagnostics: list[Diagnostic] = []
    # Each stack entry is (indent width, node whose children follow).
    stack: list[tuple[int, Node]] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
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

        statement = raw[indent:].strip()
        if not statement:
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
            # Recover at the nearest valid parent level.
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
