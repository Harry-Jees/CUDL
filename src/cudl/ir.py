"""Framework-neutral intermediate representation for CUDL documents.

The IR is a stable adapter boundary: front ends parse source into a Document,
then adapters consume this normalized, serializable tree.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .limits import MAX_NESTING_LEVEL, MAX_NODES
from .parser import Document, Node

IR_VERSION = 1

_LAYOUT_KINDS = {
    "page", "header", "content", "footer", "row", "column", "grid",
    "stack", "split", "cards", "overlay", "scroll", "space",
}
_ELEMENT_KINDS = {
    "title", "heading", "text", "paragraph", "button", "image", "video",
    "input", "icon", "divider", "spacer", "link",
}
_DECLARATION_KINDS = {"component", "theme", "style", "def", "class", "import", "script"}
_SCRIPT_BLOCKS = {"script", "js", "javascript", "python", "java", "c", "cpp", "rust", "go", "swift", "kotlin"}
_IR_CATEGORIES = frozenset({"layout", "element", "declaration", "component", "generic"})


class IRValidationError(ValueError):
    """Raised when an external payload does not satisfy the CUDL IR contract."""


@dataclass(slots=True)
class IRNode:
    """A normalized node with source provenance and ordered children."""
    kind: str
    name: str
    value: str = ""
    line: int = 1
    raw_source: str | None = None
    category: str = "generic"
    children: list["IRNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "source": {"line": self.line},
            "raw_source": self.raw_source,
            "children": [child.to_dict() for child in self.children],
        }


def _required_string(payload: Mapping[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise IRValidationError(f"IR node field '{key}' must be {qualifier}.")
    return value


def _deserialize_node(
    payload: object, *, depth: int, node_count: list[int], in_script: bool = False
) -> IRNode:
    if depth > MAX_NESTING_LEVEL:
        raise IRValidationError(
            f"IR nesting exceeds the {MAX_NESTING_LEVEL}-level safety limit."
        )
    if not isinstance(payload, Mapping):
        raise IRValidationError("Every IR node must be an object.")

    node_count[0] += 1
    if node_count[0] > MAX_NODES:
        raise IRValidationError(f"IR document exceeds the {MAX_NODES}-node safety limit.")

    kind = _required_string(payload, "kind")
    if kind != kind.casefold():
        raise IRValidationError("IR node kinds must use normalized lowercase spelling.")
    name = _required_string(payload, "name")
    value = _required_string(payload, "value", allow_empty=True)

    category = _required_string(payload, "category")
    if category not in _IR_CATEGORIES:
        raise IRValidationError(f"Unsupported IR node category: {category}.")

    source = payload.get("source")
    if not isinstance(source, Mapping):
        raise IRValidationError("IR node source provenance must be an object.")
    line = source.get("line")
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise IRValidationError("IR node source line must be a positive integer.")

    raw_source = payload.get("raw_source")
    if raw_source is not None and not isinstance(raw_source, str):
        raise IRValidationError("IR node raw_source must be a string or null.")

    children = payload.get("children")
    if not isinstance(children, list):
        raise IRValidationError("IR node children must be an array.")

    script_context = in_script or kind in _SCRIPT_BLOCKS
    deserialized_children = [
        _deserialize_node(
            child, depth=depth + 1, node_count=node_count, in_script=script_context
        )
        for child in children
    ]
    expected_category = _category(kind, in_script, bool(deserialized_children))
    if category != expected_category:
        raise IRValidationError(
            f"IR node '{kind}' category '{category}' does not match "
            f"its semantic category '{expected_category}'."
        )

    return IRNode(
        kind=kind,
        name=name,
        value=value,
        line=line,
        raw_source=raw_source,
        category=category,
        children=deserialized_children,
    )


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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "IRDocument":
        """Validate and deserialize a versioned IR payload without executing it.

        Only the current IR version is accepted. Node count, nesting, source
        provenance and field types are checked before the tree is returned.
        """
        if not isinstance(payload, Mapping):
            raise IRValidationError("A CUDL IR document must be an object.")
        if payload.get("type") != "CUDLIR":
            raise IRValidationError("IR document type must be 'CUDLIR'.")

        version = payload.get("version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise IRValidationError("IR document version must be an integer.")
        if version != IR_VERSION:
            raise IRValidationError(
                f"Unsupported CUDL IR version {version}; expected {IR_VERSION}."
            )

        source = payload.get("source")
        if source is not None and not isinstance(source, str):
            raise IRValidationError("IR document source must be a string or null.")

        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            raise IRValidationError("IR document nodes must be an array.")

        node_count = [0]
        return cls(
            nodes=[
                _deserialize_node(node, depth=0, node_count=node_count)
                for node in nodes
            ],
            source=source,
            version=version,
        )


def _category(kind: str, in_script: bool = False, has_children: bool = False) -> str:
    if in_script and kind.startswith("@"):
        return "declaration" if has_children else "generic"
    if kind in _LAYOUT_KINDS:
        return "layout"
    if kind in _ELEMENT_KINDS:
        return "element"
    if kind in _DECLARATION_KINDS:
        return "declaration"
    if kind.startswith("@"):
        return "component"
    return "generic"


def _lower_node(node: Node, in_script: bool = False) -> IRNode:
    kind = node.kind.casefold()
    script_context = in_script or kind in _SCRIPT_BLOCKS
    return IRNode(
        kind=kind,
        name=kind,
        value=node.value,
        line=node.line,
        raw_source=node.raw_source,
        category=_category(kind, in_script, bool(node.children)),
        children=[_lower_node(child, script_context) for child in node.children],
    )


def lower(document: Document) -> IRDocument:
    """Lower a parsed AST document into the versioned adapter IR."""
    return IRDocument(
        nodes=[_lower_node(node) for node in document.nodes],
        source=document.source,
    )
