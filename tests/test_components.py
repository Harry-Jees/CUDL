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
