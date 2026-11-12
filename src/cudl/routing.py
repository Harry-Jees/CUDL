"""Deterministic device-aware component routing for CUDL KIT definitions.

This module only selects declared implementations. It never imports or executes
those implementations; the selected host adapter remains responsible for them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .parser import Node


@dataclass(frozen=True, slots=True)
class DeviceContext:
    platform: str
    device: str = "any"
    width: int | None = None
    input: str | None = None
    capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class ComponentRoute:
    component: str
    platform: str
    implementation: str
    device: str = "any"
    min_width: int | None = None
    max_width: int | None = None
    input: str | None = None
    requires: frozenset[str] = frozenset()
    priority: int = 0
    line: int = 1


@dataclass(slots=True)
class RouteCompileResult:
    routes: dict[str, list[ComponentRoute]] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RouteResolution:
    component: str
    implementation: str | None
    route: ComponentRoute | None
    reason: str


def _assignment(node: Node) -> str | None:
    value = node.value.strip()
    if not value.startswith("="):
        return None
    return value[1:].strip()


def _integer(value: str | None, label: str, line: int, errors: list[str]) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except ValueError:
        errors.append(f"CUDL5002 line {line}: {label} must be a whole number.")
        return None
    if number < 0:
        errors.append(f"CUDL5002 line {line}: {label} cannot be negative.")
        return None
    return number


def compile_component_routes(nodes: Iterable[Node]) -> RouteCompileResult:
    """Read route declarations nested under KIT component declarations.

    Syntax:
        component Navigation
            route = android
                device = phone
                use = AndroidPhoneNavigation
    """
    result = RouteCompileResult()
    for component in nodes:
        if component.kind.casefold() != "component":
            continue
        component_name = component.value.strip().split(maxsplit=1)[0] if component.value.strip() else ""
        if not component_name:
            result.diagnostics.append(f"CUDL5001 line {component.line}: component route owner has no name.")
            continue

        routes: list[ComponentRoute] = []
        for route_node in component.children:
            if route_node.kind.casefold() != "route":
                continue
            platform = (_assignment(route_node) or "").casefold()
            if not platform:
                result.diagnostics.append(f"CUDL5001 line {route_node.line}: route requires '= platform'.")
                continue
            values = {child.kind.casefold(): _assignment(child) for child in route_node.children}
            implementation = values.get("use")
            if not implementation:
                result.diagnostics.append(f"CUDL5001 line {route_node.line}: route requires 'use = ImplementationName'.")
                continue
            device = (values.get("device") or "any").casefold()
            input_mode = values.get("input")
            required = frozenset(
                part.strip().casefold()
                for part in (values.get("requires") or "").split(",")
                if part.strip()
            )
            min_width = _integer(values.get("min-width"), "min-width", route_node.line, result.diagnostics)
            max_width = _integer(values.get("max-width"), "max-width", route_node.line, result.diagnostics)
            priority = _integer(values.get("priority"), "priority", route_node.line, result.diagnostics) or 0
            if min_width is not None and max_width is not None and min_width > max_width:
                result.diagnostics.append(f"CUDL5003 line {route_node.line}: min-width cannot exceed max-width.")
                continue
            routes.append(ComponentRoute(
                component=component_name,
                platform=platform,
                implementation=implementation,
                device=device,
                min_width=min_width,
                max_width=max_width,
                input=input_mode.casefold() if input_mode else None,
                requires=required,
                priority=priority,
                line=route_node.line,
            ))
        if routes:
            result.routes[component_name.casefold()] = routes
    return result


def _matches(route: ComponentRoute, device: DeviceContext) -> bool:
    platform_match = route.platform == "default" or route.platform == device.platform.casefold()
    device_match = route.device == "any" or route.device == device.device.casefold()
    width_match = (
        (route.min_width is None or (device.width is not None and device.width >= route.min_width))
        and (route.max_width is None or (device.width is not None and device.width <= route.max_width))
    )
    input_match = route.input is None or route.input == (device.input or "").casefold()
    capability_match = route.requires.issubset({item.casefold() for item in device.capabilities})
    return platform_match and device_match and width_match and input_match and capability_match


def resolve_component_route(
    component: str,
    routes: dict[str, list[ComponentRoute]],
    device: DeviceContext,
) -> RouteResolution:
    """Choose the most specific compatible route, then use the default route."""
    candidates = [
        route for route in routes.get(component.casefold(), [])
        if route.platform != "default" and _matches(route, device)
    ]
    if candidates:
        candidates.sort(key=lambda item: (
            item.device != "any",
            item.min_width is not None or item.max_width is not None,
            item.input is not None,
            len(item.requires),
            item.priority,
        ), reverse=True)
        chosen = candidates[0]
        return RouteResolution(component, chosen.implementation, chosen, "matched platform/device route")

    fallback = [
        route for route in routes.get(component.casefold(), [])
        if route.platform == "default" and _matches(route, device)
    ]
    if fallback:
        fallback.sort(key=lambda item: item.priority, reverse=True)
        chosen = fallback[0]
        return RouteResolution(component, chosen.implementation, chosen, "matched default route")
    return RouteResolution(component, None, None, "no compatible route or default implementation")


def compile_global_routes(nodes: Iterable[Node]) -> RouteCompileResult:
    """Compile GUIDE-level route maps.

    Syntax:
        route = android
            component = Navigation
            device = phone
            use = AndroidPhoneNavigation

    Global routes are useful for routing several components from one place.
    Component-local routes can override them through merge_route_tables().
    """
    synthetic: list[Node] = []
    for route_node in nodes:
        if route_node.kind.casefold() != "route":
            continue
        component = next(
            (_assignment(child) for child in route_node.children
             if child.kind.casefold() == "component"),
            None,
        )
        if not component:
            result.diagnostics.append(
                f"CUDL5004 line {route_node.line}: GUIDE global route requires 'component = ComponentName'."
            )
            continue
        route_children = [
            child for child in route_node.children
            if child.kind.casefold() != "component"
        ]
        synthetic.append(Node(
            kind="component",
            value=component,
            children=[Node(
                kind="route",
                value=route_node.value,
                children=route_children,
                line=route_node.line,
            )],
            line=route_node.line,
        ))
    return compile_component_routes(synthetic)


def merge_route_tables(
    global_routes: dict[str, list[ComponentRoute]],
    component_routes: dict[str, list[ComponentRoute]],
) -> dict[str, list[ComponentRoute]]:
    """Merge global and local routes; local declarations win equal matches."""
    merged = {name: list(items) for name, items in global_routes.items()}
    for name, items in component_routes.items():
        # Local routes are placed first so stable tie-breaking prefers them,
        # while an explicitly higher priority still wins.
        merged[name] = list(items) + merged.get(name, [])
    return merged



def compile_application_routes(bundle) -> RouteCompileResult:
    """Compile GUIDE global routes and KIT component routes from one bundle."""
    sections = getattr(bundle, "sections", {})
    guide_result = compile_global_routes(sections.get("guide", ()))
    kit_result = compile_component_routes(sections.get("kit", ()))
    return RouteCompileResult(
        routes=merge_route_tables(guide_result.routes, kit_result.routes),
        diagnostics=[*guide_result.diagnostics, *kit_result.diagnostics],
    )
