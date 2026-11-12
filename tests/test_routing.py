from cudl.parser import parse
from cudl.bundle import parse_bundle
from cudl.routing import (DeviceContext, compile_application_routes, compile_component_routes, compile_global_routes, merge_route_tables, resolve_component_route)


def _routes(source):
    parsed = parse(source)
    assert not parsed.has_errors
    kit = next(node for node in parsed.document.nodes if node.kind == "kit")
    return compile_component_routes(kit.children)


def test_selects_platform_and_device_specific_implementation():
    result = _routes(
        "KIT\n"
        "    component Navigation\n"
        "        route = android\n"
        "            device = phone\n"
        "            use = AndroidPhoneNavigation\n"
        "        route = android\n"
        "            device = tablet\n"
        "            use = AndroidTabletNavigation\n"
        "        route = web\n"
        "            use = WebNavigation\n"
        "        route = default\n"
        "            use = ResponsiveNavigation\n"
    )
    assert not result.diagnostics
    phone = resolve_component_route("Navigation", result.routes, DeviceContext("android", "phone", 390))
    tablet = resolve_component_route("Navigation", result.routes, DeviceContext("android", "tablet", 900))
    web = resolve_component_route("Navigation", result.routes, DeviceContext("web", "desktop", 1440))
    assert phone.implementation == "AndroidPhoneNavigation"
    assert tablet.implementation == "AndroidTabletNavigation"
    assert web.implementation == "WebNavigation"


def test_uses_default_route_when_platform_has_no_match():
    result = _routes(
        "KIT\n"
        "    component Header\n"
        "        route = android\n"
        "            use = AndroidHeader\n"
        "        route = default\n"
        "            use = UniversalHeader\n"
    )
    resolution = resolve_component_route("Header", result.routes, DeviceContext("ios", "phone"))
    assert resolution.implementation == "UniversalHeader"
    assert resolution.reason == "matched default route"


def test_prefers_more_specific_rule_and_checks_capabilities():
    result = _routes(
        "KIT\n"
        "    component Panel\n"
        "        route = android\n"
        "            use = GenericAndroidPanel\n"
        "        route = android\n"
        "            device = tablet\n"
        "            requires = stylus, multitouch\n"
        "            use = TabletPanel\n"
    )
    no_capability = resolve_component_route("Panel", result.routes, DeviceContext("android", "tablet"))
    with_capability = resolve_component_route(
        "Panel", result.routes, DeviceContext("android", "tablet", capabilities=frozenset({"stylus", "multitouch"}))
    )
    assert no_capability.implementation == "GenericAndroidPanel"
    assert with_capability.implementation == "TabletPanel"


def test_reports_invalid_route_width_range_and_missing_implementation():
    result = _routes(
        "KIT\n"
        "    component Panel\n"
        "        route = android\n"
        "            min-width = 900\n"
        "            max-width = 400\n"
        "            use = BrokenPanel\n"
        "        route = ios\n"
    )
    assert any("min-width cannot exceed max-width" in item for item in result.diagnostics)
    assert any("route requires 'use" in item for item in result.diagnostics)


def test_route_resolution_is_case_insensitive_for_keywords_and_names():
    result = _routes(
        "kIt\n"
        "    CoMpOnEnT Navigation\n"
        "        RoUtE = AnDrOiD\n"
        "            DeViCe = PhOnE\n"
        "            UsE = MobileNavigation\n"
    )
    resolution = resolve_component_route("navigation", result.routes, DeviceContext("ANDROID", "PHONE"))
    assert resolution.implementation == "MobileNavigation"


def test_supports_global_route_map_and_local_component_override():
    guide = parse(
        "GUIDE\n"
        "    route = android\n"
        "        component = Navigation\n"
        "        use = GlobalAndroidNavigation\n"
        "    route = default\n"
        "        component = Navigation\n"
        "        use = GlobalFallbackNavigation\n"
    )
    kit = parse(
        "KIT\n"
        "    component Navigation\n"
        "        route = android\n"
        "            use = LocalAndroidNavigation\n"
    )
    global_result = compile_global_routes(guide.document.nodes[0].children)
    local_result = compile_component_routes(kit.document.nodes[0].children)
    assert not global_result.diagnostics
    assert not local_result.diagnostics
    combined = merge_route_tables(global_result.routes, local_result.routes)
    result = resolve_component_route("Navigation", combined, DeviceContext("android", "phone"))
    assert result.implementation == "LocalAndroidNavigation"


def test_global_route_map_uses_default_for_unlisted_platform():
    guide = parse(
        "GUIDE\n"
        "    route = default\n"
        "        component = Header\n"
        "        use = UniversalHeader\n"
    )
    routes = compile_global_routes(guide.document.nodes[0].children)
    result = resolve_component_route("Header", routes.routes, DeviceContext("ios", "tablet"))
    assert result.implementation == "UniversalHeader"


def test_compiles_global_and_local_routes_from_complete_application():
    parsed = parse_bundle(
        "GUIDE\n"
        "    route = android\n"
        "        component = Header\n"
        "        use = GlobalHeader\n"
        "KIT\n"
        "    component Header\n"
        "        route = android\n"
        "            use = LocalHeader\n"
        "PAGES\n"
        "    page Home\n"
    )
    assert not parsed.has_errors
    result = compile_application_routes(parsed.bundle)
    assert not result.diagnostics
    resolution = resolve_component_route("Header", result.routes, DeviceContext("android"))
    assert resolution.implementation == "LocalHeader"


def test_global_route_requires_component_assignment():
    guide = parse(
        "GUIDE\n"
        "    route = android\n"
        "        use = UnscopedAndroidRoute\n"
    )
    result = compile_global_routes(guide.document.nodes[0].children)
    assert any("requires 'component" in item for item in result.diagnostics)
