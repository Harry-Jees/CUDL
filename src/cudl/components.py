"""Component declarations, properties, and reference validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from .diagnostics import Diagnostic, Severity
from .modules import ModuleGraph

@dataclass(frozen=True, slots=True)
class ComponentProperty:
    name: str
    required: bool = True
    line: int = 1

@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    name: str
    module: str
    line: int
    properties: tuple[ComponentProperty, ...] = ()

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
                    name: {
                        "name": item.name, "module": item.module, "line": item.line,
                        "properties": [
                            {"name": prop.name, "required": prop.required, "line": prop.line}
                            for prop in item.properties
                        ],
                    }
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
    return name if all(char.isalnum() or char == "_" for char in name) else None

def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.children)

def _property_declarations(component, path: str, diagnostics: list[Diagnostic]):
    properties = []
    seen = set()
    for child in component.children:
        if child.kind.casefold() != "property":
            continue
        parts = child.value.split()
        name = parts[0] if parts else ""
        valid = bool(name) and (name[0].isalpha() or name[0] == "_") and all(
            char.isalnum() or char == "_" for char in name
        )
        if not valid:
            diagnostics.append(Diagnostic(
                code="CUDL3005", message="Property declaration requires a valid name.",
                severity=Severity.ERROR, line=child.line, source=path,
                suggestion="Use: property name or property name optional.",
            ))
            continue
        key = name.casefold()
        if key in seen:
            diagnostics.append(Diagnostic(
                code="CUDL3006", message=f"Property {name!r} is declared more than once.",
                severity=Severity.ERROR, line=child.line, source=path,
                suggestion="Give each component property a unique name.",
            ))
            continue
        if len(parts) > 2 or (len(parts) == 2 and parts[1].casefold() != "optional"):
            diagnostics.append(Diagnostic(
                code="CUDL3007", message=f"Invalid property declaration for {name!r}.",
                severity=Severity.ERROR, line=child.line, source=path,
                suggestion="Use: property name or property name optional.",
            ))
            continue
        seen.add(key)
        properties.append(ComponentProperty(name, len(parts) == 1, child.line))
    return tuple(properties)

def _validate_instance(node, definition, path, diagnostics):
    declared = {item.name.casefold(): item for item in definition.properties}
    supplied = set()
    for child in node.children:
        key = child.kind.casefold()
        if not child.value.startswith("="):
            continue
        if key not in declared:
            diagnostics.append(Diagnostic(
                code="CUDL3008",
                message=f"Unknown property {child.kind!r} for component {definition.name}.",
                severity=Severity.ERROR, line=child.line, source=path,
                suggestion="Use a declared component property or correct its name.",
            ))
            continue
        if key in supplied:
            diagnostics.append(Diagnostic(
                code="CUDL3009", message=f"Property {child.kind!r} is supplied more than once.",
                severity=Severity.ERROR, line=child.line, source=path,
                suggestion="Keep only one assignment for each component property.",
            ))
            continue
        supplied.add(key)
    for key, prop in declared.items():
        if prop.required and key not in supplied:
            diagnostics.append(Diagnostic(
                code="CUDL3010",
                message=f"Required property {prop.name!r} is missing for component {definition.name}.",
                severity=Severity.ERROR, line=node.line, source=path,
                suggestion=f'Pass a value with: {prop.name} = "..."',
            ))

def build_component_registry(graph: ModuleGraph) -> ComponentRegistry:
    """Collect definitions and validate imports, references, and property bindings.

    Direct component children may declare properties with: property title
    or property subtitle optional. Instances supply values with title = "text".
    """
    registry = ComponentRegistry()
    for path, record in sorted(graph.modules.items()):
        declared = {}
        for node in record.document.nodes:
            if node.kind.casefold() != "component":
                continue
            name = _component_name(node.value)
            if name is None:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3001", message="Component declaration requires a valid name.",
                    severity=Severity.ERROR, line=node.line, source=path,
                    suggestion="Use: component ProfileCard",
                ))
                continue
            key = name.casefold()
            if key in declared:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3002", message=f"Component {name!r} is declared more than once in {path}.",
                    severity=Severity.ERROR, line=node.line, source=path,
                    suggestion="Give each component in a module a unique name.",
                ))
                continue
            declared[key] = ComponentDefinition(
                name, path, node.line, _property_declarations(node, path, registry.diagnostics)
            )
        registry.definitions[path] = declared

    for path, record in sorted(graph.modules.items()):
        visible = dict(registry.definitions.get(path, {}))
        for imported in record.imports:
            target = registry.definitions.get(imported.target, {})
            for binding in imported.spec.bindings:
                source_key = binding.name.casefold()
                alias = (binding.alias or binding.name).casefold()
                if source_key not in target:
                    registry.diagnostics.append(Diagnostic(
                        code="CUDL3003",
                        message=f"{binding.name!r} is not a component declared by {imported.target}.",
                        severity=Severity.ERROR,
                        line=next((n.line for n in record.document.nodes if n.kind.casefold() == "import" and imported.spec.source in n.value), 1),
                        source=path,
                        suggestion="Import a declared component name, or add it to the target module.",
                    ))
                    continue
                visible[alias] = target[source_key]

        for node in _walk(record.document.nodes):
            if not node.kind.startswith("@"):
                continue
            definition = visible.get(node.kind[1:].casefold())
            if definition is None:
                registry.diagnostics.append(Diagnostic(
                    code="CUDL3004", message=f"Unknown component reference: {node.kind}.",
                    severity=Severity.ERROR, line=node.line, source=path,
                    suggestion='Declare the component or import it with: import {Name} from "KIT/components".',
                ))
            else:
                _validate_instance(node, definition, path, registry.diagnostics)
    return registry
