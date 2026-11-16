"""Project module import parsing and dependency resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
import posixpath
import re
from typing import Mapping

from .diagnostics import Diagnostic, Severity
from .parser import Document, parse

_IMPORT = re.compile(r"""^\{(?P<names>[^}]*)\}\s+from\s+(?P<quote>["'])(?P<source>.+?)(?P=quote)$""", re.IGNORECASE)
_SIMPLE_IMPORT = re.compile(r"""^(?P<quote>["'])(?P<source>.+?)(?P=quote)$""")
_SECTIONS = {"guide": "GUIDE", "kit": "KIT", "pages": "PAGES", "scripts": "SCRIPTS"}


@dataclass(frozen=True, slots=True)
class ImportBinding:
    name: str
    alias: str | None = None


@dataclass(frozen=True, slots=True)
class ImportSpec:
    source: str
    bindings: tuple[ImportBinding, ...] = ()


@dataclass(slots=True)
class ResolvedImport:
    spec: ImportSpec
    target: str


@dataclass(slots=True)
class ModuleRecord:
    path: str
    document: Document
    imports: list[ResolvedImport] = field(default_factory=list)


@dataclass(slots=True)
class ModuleGraph:
    entry: str
    modules: dict[str, ModuleRecord]
    order: list[str]
    diagnostics: list[Diagnostic]

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLModuleGraph",
            "version": 1,
            "entry": self.entry,
            "order": list(self.order),
            "modules": {
                path: {
                    "imports": [
                        {
                            "source": item.spec.source,
                            "target": item.target,
                            "bindings": [
                                {"name": binding.name, "alias": binding.alias}
                                for binding in item.spec.bindings
                            ],
                        }
                        for item in record.imports
                    ]
                }
                for path, record in sorted(self.modules.items())
            },
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def parse_import(statement: str) -> ImportSpec:
    """Parse one import payload, including optional aliases."""
    value = statement.strip()
    match = _IMPORT.match(value)
    if match:
        bindings: list[ImportBinding] = []
        for item in match.group("names").split(","):
            part = item.strip()
            if not part:
                continue
            pieces = re.split(r"\s+as\s+", part, maxsplit=1, flags=re.IGNORECASE)
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", pieces[0]):
                raise ValueError(f"Invalid imported name: {pieces[0]!r}")
            alias = pieces[1].strip() if len(pieces) == 2 else None
            if alias is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias):
                raise ValueError(f"Invalid import alias: {alias!r}")
            bindings.append(ImportBinding(pieces[0], alias))
        if not bindings:
            raise ValueError("An import must contain at least one named binding.")
        return ImportSpec(match.group("source"), tuple(bindings))

    match = _SIMPLE_IMPORT.match(value)
    if match:
        return ImportSpec(match.group("source"))
    raise ValueError('Expected: import {Name} from "KIT/buttons"')


def _candidate_paths(importer: str, source: str) -> list[str]:
    raw = source.replace("\\", "/").strip()
    if not raw:
        return []
    section, separator, remainder = raw.partition("/")
    if section.casefold() in _SECTIONS:
        base = _SECTIONS[section.casefold()] + (separator + remainder if separator else "")
    else:
        base = posixpath.join(posixpath.dirname(importer), raw)
    base = posixpath.normpath(base).lstrip("/")
    candidates = [base] if base.endswith(".cudl") else [
        base + ".cudl",
        posixpath.join(base, "module.cudl"),
        posixpath.join(base, "index.cudl"),
    ]
    return list(dict.fromkeys(posixpath.normpath(item) for item in candidates))


def resolve_project(sources: Mapping[str, str], entry: str) -> ModuleGraph:
    """Resolve reachable imports from a project-relative entry path."""
    normalized = {
        posixpath.normpath(path.replace("\\", "/")): text
        for path, text in sources.items()
    }
    entry_path = posixpath.normpath(entry.replace("\\", "/"))
    diagnostics: list[Diagnostic] = []
    modules: dict[str, ModuleRecord] = {}
    visiting: list[str] = []
    visited: set[str] = set()
    order: list[str] = []

    if entry_path not in normalized:
        return ModuleGraph(entry_path, {}, [], [Diagnostic(
            code="CUDL2001",
            message=f"Entry module not found: {entry_path}",
            severity=Severity.ERROR,
            line=1,
            source=entry_path,
            suggestion="Check the entry path relative to the project root.",
        )])

    def visit(path: str) -> None:
        if path in visited:
            return
        if path in visiting:
            cycle = visiting[visiting.index(path):] + [path]
            diagnostics.append(Diagnostic(
                code="CUDL2003",
                message="Circular module dependency: " + " -> ".join(cycle),
                severity=Severity.ERROR,
                line=1,
                source=path,
                suggestion="Extract shared declarations into a separate module.",
            ))
            return

        visiting.append(path)
        result = parse(normalized[path], source=path)
        diagnostics.extend(result.diagnostics)
        record = ModuleRecord(path, result.document)
        modules[path] = record

        for node in result.document.nodes:
            if node.kind.casefold() != "import":
                continue
            try:
                spec = parse_import(node.value)
            except ValueError as exc:
                diagnostics.append(Diagnostic(
                    code="CUDL2002",
                    message=str(exc),
                    severity=Severity.ERROR,
                    line=node.line,
                    source=path,
                    suggestion='Use import {Name} from "KIT/buttons".',
                ))
                continue
            candidates = _candidate_paths(path, spec.source)
            target = next((candidate for candidate in candidates if candidate in normalized), None)
            if target is None:
                diagnostics.append(Diagnostic(
                    code="CUDL2004",
                    message=f"Cannot resolve import {spec.source!r} from {path}.",
                    severity=Severity.ERROR,
                    line=node.line,
                    source=path,
                    suggestion="Check the module path and ensure its .cudl file exists.",
                ))
                continue
            record.imports.append(ResolvedImport(spec, target))
            visit(target)

        visiting.pop()
        visited.add(path)
        order.append(path)

    visit(entry_path)
    return ModuleGraph(entry_path, modules, order, diagnostics)
