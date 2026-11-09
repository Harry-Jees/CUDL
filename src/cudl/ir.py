"""Framework-neutral intermediate representation for CUDL documents.

The IR is a stable adapter boundary: front ends parse source into a Document,
then adapters consume this normalized, serializable tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .parser import Document, Node

IR_VERSION = 1

# These are semantic categories, not reserved words. Unknown names remain
# generic nodes so user-defined components can pass through the IR unchanged.
_LAYOUT_KINDS = {
    "page", "header", "content", "footer", "row", "column", "grid",
    "stack", "split", "cards", "overlay", "scroll", "space",
}
_ELEMENT_KINDS = {
    "title", "heading", "text", "paragraph", "button", "image", "video",
    "input", "icon", "divider", "spacer", "link",
}
_DECLARATION_KINDS = {"component", "theme", "style", "def", "class", "import"}


@dataclass(slots=True)
class IRNode:
    """A normalized node with source provenance and ordered children."""
    kind: str
    name: str
    value: str = ""
    line: int = 1
    category: str = "generic"
    children: list["IRNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "source": {"line": self.line},
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(slots=True)
class IRDocument:
    """Versioned document consumed by host-framework adapters."""
    nodes: list[IRNode]
    source: str | None = None
    version: int = IR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "CUDLIR",
            "version": self.version,
            "source": self.source,
            "nodes": [node.to_dict() for node in self.nodes],
        }


def _category(kind: str) -> str:
    if kind in _LAYOUT_KINDS:
        return "layout"
    if kind in _ELEMENT_KINDS:
        return "element"
    if kind in _DECLARATION_KINDS:
        return "declaration"
    if kind.startswith("@"):
        return "component"
    return "generic"


def _lower_node(node: Node) -> IRNode:
    kind = node.kind.casefold()
    return IRNode(
        kind=kind,
        name=kind,
        value=node.value,
        line=node.line,
        category=_category(kind),
        children=[_lower_node(child) for child in node.children],
    )


def lower(document: Document) -> IRDocument:
    """Lower a parsed AST document into the versioned adapter IR."""
    return IRDocument(
        nodes=[_lower_node(node) for node in document.nodes],
        source=document.source,
    )
