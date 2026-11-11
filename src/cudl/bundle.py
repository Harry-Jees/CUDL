"""Five-part application bundle parsing and lowering.

The generic parser remains backward-compatible. This module adds the
application-level contract: an optional `bundle Name` wrapper containing
GUIDE, KIT, PAGES, SCRIPTS and TIME peer sections in canonical order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .diagnostics import Diagnostic, Severity
from .ir import IRDocument, lower
from .parser import Document, Node, parse

SECTION_ORDER = ("guide", "kit", "pages", "scripts", "time")
_SECTION_SET = frozenset(SECTION_ORDER)


@dataclass(slots=True)
class ApplicationBundle:
    """Validated five-part source bundle with source-preserving section nodes."""

    name: str | None
    sections: dict[str, list[Node]]
    source: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLBundle",
            "version": 1,
            "name": self.name,
            "source": self.source,
            "sections": {
                name: [node.to_dict() for node in self.sections[name]]
                for name in SECTION_ORDER
                if name in self.sections
            },
        }


@dataclass(slots=True)
class BundleParseResult:
    bundle: ApplicationBundle
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self.diagnostics)


@dataclass(slots=True)
class ApplicationIR:
    """Versioned unified IR with explicitly typed top-level section payloads."""

    name: str | None
    sections: dict[str, IRDocument]
    source: str | None = None
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "CUDLApplicationIR",
            "version": self.version,
            "name": self.name,
            "source": self.source,
            "sections": {
                name: self.sections[name].to_dict()
                for name in SECTION_ORDER
                if name in self.sections
            },
        }


def parse_bundle(source_text: str, source: str | None = None) -> BundleParseResult:
    """Parse and validate an application bundle without changing legacy parse()."""
    parsed = parse(source_text, source=source)
    diagnostics = list(parsed.diagnostics)
    roots = list(parsed.document.nodes)
    bundle_name: str | None = None

    wrappers = [node for node in roots if node.kind.casefold() == "bundle"]
    if wrappers:
        if len(wrappers) > 1:
            diagnostics.append(Diagnostic(
                code="CUDL2001",
                message="An application may contain only one bundle declaration.",
                severity=Severity.ERROR,
                line=wrappers[1].line,
                source=source,
                suggestion="Keep one bundle declaration and move all five sections inside it.",
            ))
        if len(roots) != 1:
            extra = next((node for node in roots if node.kind.casefold() != "bundle"), None)
            if extra is None:
                extra = wrappers[1]
            diagnostics.append(Diagnostic(
                code="CUDL2002",
                message="A bundle declaration must be the only root-level statement.",
                severity=Severity.ERROR,
                line=extra.line,
                source=source,
                suggestion="Move GUIDE, KIT, PAGES, SCRIPTS and TIME inside the bundle block.",
            ))
        wrapper = wrappers[0]
        bundle_name = wrapper.value.strip() or None
        roots = list(wrapper.children)

    sections: dict[str, list[Node]] = {}
    seen_order: list[tuple[str, int]] = []
    for node in roots:
        section_name = node.kind.casefold()
        if section_name not in _SECTION_SET:
            diagnostics.append(Diagnostic(
                code="CUDL2003",
                message=f"Unexpected top-level statement {node.kind!r}; expected one of GUIDE, KIT, PAGES, SCRIPTS or TIME.",
                severity=Severity.ERROR,
                line=node.line,
                source=source,
                suggestion="Place application content inside one of the five named sections.",
            ))
            continue
        if section_name in sections:
            diagnostics.append(Diagnostic(
                code="CUDL2004",
                message=f"The {section_name.upper()} section may appear only once.",
                severity=Severity.ERROR,
                line=node.line,
                source=source,
                suggestion=f"Combine all {section_name.upper()} declarations into the first section.",
            ))
            continue
        sections[section_name] = list(node.children)
        seen_order.append((section_name, node.line))

    positions = {name: index for index, name in enumerate(SECTION_ORDER)}
    previous = -1
    for name, line in seen_order:
        current = positions[name]
        if current < previous:
            diagnostics.append(Diagnostic(
                code="CUDL2005",
                message=f"The {name.upper()} section is out of canonical order.",
                severity=Severity.ERROR,
                line=line,
                source=source,
                suggestion="Order sections as GUIDE, KIT, PAGES, SCRIPTS, TIME.",
            ))
        previous = max(previous, current)

    if not sections:
        diagnostics.append(Diagnostic(
            code="CUDL2006",
            message="No valid CUDL application sections were found.",
            severity=Severity.ERROR,
            line=1,
            source=source,
            suggestion="Add at least one of GUIDE, KIT, PAGES, SCRIPTS or TIME.",
        ))

    return BundleParseResult(
        bundle=ApplicationBundle(name=bundle_name, sections=sections, source=source),
        diagnostics=diagnostics,
    )


def lower_bundle(bundle: ApplicationBundle) -> ApplicationIR:
    """Lower each peer section through the shared framework-neutral node IR."""
    lowered = {
        name: lower(Document(nodes=nodes, source=bundle.source))
        for name, nodes in bundle.sections.items()
    }
    return ApplicationIR(
        name=bundle.name,
        sections=lowered,
        source=bundle.source,
    )
