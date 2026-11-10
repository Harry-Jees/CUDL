from cudl.components import build_component_registry
from cudl.modules import resolve_project


def test_collects_local_components_and_validates_references():
    graph = resolve_project(
        {
            "PAGES/home.cudl": (
                "component LocalCard\n"
                "page Home\n"
                "    @LocalCard\n"
                "    @MissingCard\n"
            )
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert "localcard" in registry.definitions["PAGES/home.cudl"]
    assert [item.code for item in registry.diagnostics] == ["CUDL3004"]


def test_imported_component_alias_is_visible():
    graph = resolve_project(
        {
            "PAGES/home.cudl": (
                'import {ProfileCard as Card} from "KIT/profile"\n'
                "page Home\n"
                "    @Card\n"
            ),
            "KIT/profile.cudl": "component ProfileCard\n",
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert not registry.has_errors
    assert registry.definitions["KIT/profile.cudl"]["profilecard"].name == "ProfileCard"


def test_importing_unknown_component_is_reported():
    graph = resolve_project(
        {
            "PAGES/home.cudl": 'import {Ghost} from "KIT/profile"\n',
            "KIT/profile.cudl": "component ProfileCard\n",
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3003" for item in registry.diagnostics)


def test_duplicate_component_declaration_is_reported():
    graph = resolve_project(
        {"KIT/cards.cudl": "component Card\ncomponent Card\n"},
        "KIT/cards.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3002" for item in registry.diagnostics)


def test_invalid_component_declaration_is_reported():
    graph = resolve_project(
        {"KIT/cards.cudl": "component\n"},
        "KIT/cards.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3001" for item in registry.diagnostics)


def test_required_and_optional_component_properties():
    graph = resolve_project(
        {
            "KIT/profile.cudl": (
                "component ProfileCard\n"
                "    property name\n"
                "    property subtitle optional\n"
            ),
            "PAGES/home.cudl": (
                'import {ProfileCard} from "KIT/profile"\n'
                "page Home\n"
                "    @ProfileCard\n"
                "        name = Harry\n"
            ),
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    definition = registry.definitions["KIT/profile.cudl"]["profilecard"]
    assert [(p.name, p.required) for p in definition.properties] == [
        ("name", True), ("subtitle", False)
    ]
    assert not registry.has_errors


def test_missing_required_component_property_is_reported():
    graph = resolve_project(
        {
            "KIT/profile.cudl": "component ProfileCard\n    property name\n",
            "PAGES/home.cudl": (
                'import {ProfileCard} from "KIT/profile"\n'
                "page Home\n"
                "    @ProfileCard\n"
            ),
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3010" for item in registry.diagnostics)


def test_unknown_component_instance_property_is_reported():
    graph = resolve_project(
        {
            "KIT/profile.cudl": "component ProfileCard\n    property name\n",
            "PAGES/home.cudl": (
                'import {ProfileCard} from "KIT/profile"\n'
                "page Home\n"
                "    @ProfileCard\n"
                "        title = Unexpected\n"
                "        name = Harry\n"
            ),
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3008" for item in registry.diagnostics)


def test_duplicate_component_property_is_reported():
    graph = resolve_project(
        {
            "KIT/profile.cudl": (
                "component ProfileCard\n"
                "    property name\n"
                "    property name\n"
            )
        },
        "KIT/profile.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3006" for item in registry.diagnostics)


def test_component_properties_accept_hash_data_paths_and_literals():
    graph = resolve_project(
        {
            "KIT/profile.cudl": (
                "component ProfileCard\n"
                "    property name\n"
                "    property active\n"
            ),
            "PAGES/home.cudl": (
                'import {ProfileCard} from "KIT/profile"\n'
                "page Home\n"
                "    @ProfileCard\n"
                "        name = #user.profile.name\n"
                "        active = true\n"
            ),
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert not registry.has_errors


def test_component_properties_reject_malformed_hash_paths():
    graph = resolve_project(
        {
            "KIT/profile.cudl": "component ProfileCard\n    property name\n",
            "PAGES/home.cudl": (
                'import {ProfileCard} from "KIT/profile"\n'
                "page Home\n"
                "    @ProfileCard\n"
                "        name = #user.name + 'x'\n"
            ),
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert any(item.code == "CUDL3011" for item in registry.diagnostics)


def test_at_functions_inside_script_are_not_component_references():
    graph = resolve_project(
        {
            "PAGES/home.cudl": (
                "page Home\n"
                "    script\n"
                "        @greet #person\n"
                "            print Hello #person\n"
                "        greet Harry\n"
            )
        },
        "PAGES/home.cudl",
    )
    registry = build_component_registry(graph)
    assert not registry.has_errors
