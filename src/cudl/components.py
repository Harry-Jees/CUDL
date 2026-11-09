"""Component declaration registry and reference validation.

This pass deliberately validates names and imports only. Component property
binding and host rendering are handled by later semantic/runtime layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .diagnostics import Diagnostic, Severity
from .modules import ModuleGraph


@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    name: str
    module: str
    line: int


@dataclass(slots=True)
class ComponentRegistry:
    definitions: dict[str, dict[str, ComponentDefinition]] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLComponentRegistry",
            "version": 1,
            "modules": {
                path: {
                    name: {"name": item.name, "module": item.module, "line": item.line}
                    for name, item in sorted(items.items())
                }
                for path, items in sorted(self.definitions.items())
            },
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _component_name(value: str) -> str | None:
    name = value.strip().split(maxsplit=1)[0] if value.strip() else ""
    if not name or not (name[0].isalpha() or name[0] == "_"):
        return None
    if not all(char.isalnum() or char == "_" for char in name):
        return None
    return name


def build_component_registry(graph: ModuleGraph) -> ComponentRegistry:
    """Collect component declarations and validate imports/references.

    Component names are case-insensitive within CUDL. Named imports expose
    their original name or alias in the importing module. Components declared
    in a module are local to that module unless imported elsewhere.
    """
    registry = ComponentRegistry()
    for path, record in sorted(graph.modules.items()):
        declared: dict[str, ComponentDefinition] = {}
        for node in record.document.nodes:
            if node.kind.casefold() != "component":
                continue
            name = _component_name(node.value)
            if name is None:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3001",
                    message="Component declaration requires a valid name.",
                    severity=Severity.ERROR,
                    line=node.line,
                    source=path,
                    suggestion="Use: component ProfileCard",
                ))
                continue
            key = name.casefold()
            if key in declared:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3002",
                    message=f"Component {name!r} is declared more than once in {path}.",
                    severity=Severity.ERROR,
                    line=node.line,
                    source=path,
                    suggestion="Give each component in a module a unique name.",
                ))
                continue
            declared[key] = ComponentDefinition(name, path, node.line)
        registry.definitions[path] = declared

    for path, record in sorted(graph.modules.items()):
        visible = dict(registry.definitions.get(path, {}))
        for imported in record.imports:
            target_definitions = registry.definitions.get(imported.target, {})
            for binding in imported.spec.bindings:
                source_key = binding.name.casefold()
                alias = (binding.alias or binding.name).casefold()
                if source_key not in target_definitions:
                    registry.diagnostics.append(Diagnostic(
                        code="CUDL3003",
                        message=f"{binding.name!r} is not a component declared by {imported.target}.",
                        severity=Severity.ERROR,
                        line=next((n.line for n in record.document.nodes if n.kind.casefold() == "import" and imported.spec.source in n.value), 1),
                        source=path,
                        suggestion="Import a declared component name, or add the component to the target module.",
                    ))
                    continue
                visible[alias] = target_definitions[source_key]

        for node in record.document.nodes:
            if not node.kind.startswith("@"):
                continue
            reference = node.kind[1:].casefold()
            if reference not in visible:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3004",
                    message=f"Unknown component reference: {node.kind}.",
                    severity=Severity.ERROR,
                    line=node.line,
                    source=path,
                    suggestion='Declare the component in this module or import it with: import {Name} from "KIT/components".',
                ))

    return registry
