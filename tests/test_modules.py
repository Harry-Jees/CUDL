from cudl.modules import parse_import, resolve_project


def test_parses_named_imports_and_aliases():
    spec = parse_import('{PrimaryButton, Nav as Navigation} from "KIT/buttons"')
    assert spec.source == "KIT/buttons"
    assert [(item.name, item.alias) for item in spec.bindings] == [
        ("PrimaryButton", None),
        ("Nav", "Navigation"),
    ]


def test_resolves_transitive_project_imports():
    graph = resolve_project(
        {
            "PAGES/home.cudl": (
                'import {PrimaryButton} from "KIT/buttons"\n'
                "page Home\n"
            ),
            "KIT/buttons.cudl": (
                'import {format_name} from "SCRIPTS/text"\n'
                "component PrimaryButton\n"
            ),
            "SCRIPTS/text.cudl": "def format_name()\n",
        },
        "PAGES/home.cudl",
    )
    assert not graph.has_errors
    assert graph.order == [
        "SCRIPTS/text.cudl",
        "KIT/buttons.cudl",
        "PAGES/home.cudl",
    ]
    assert graph.modules["PAGES/home.cudl"].imports[0].target == "KIT/buttons.cudl"


def test_reports_missing_import_without_crashing():
    graph = resolve_project(
        {"PAGES/home.cudl": 'import {Missing} from "KIT/missing"\npage Home\n'},
        "PAGES/home.cudl",
    )
    assert graph.has_errors
    assert graph.diagnostics[0].code == "CUDL2004"


def test_reports_circular_dependencies():
    graph = resolve_project(
        {
            "KIT/a.cudl": 'import {B} from "./b"\ncomponent A\n',
            "KIT/b.cudl": 'import {A} from "./a"\ncomponent B\n',
        },
        "KIT/a.cudl",
    )
    assert graph.has_errors
    assert any(item.code == "CUDL2003" for item in graph.diagnostics)


def test_reports_invalid_import_syntax():
    graph = resolve_project(
        {"PAGES/home.cudl": 'import {Bad-Name} from "KIT/buttons"\n'},
        "PAGES/home.cudl",
    )
    assert graph.has_errors
    assert graph.diagnostics[0].code == "CUDL2002"


def test_missing_entry_is_diagnostic():
    graph = resolve_project({}, "PAGES/home.cudl")
    assert graph.has_errors
    assert graph.diagnostics[0].code == "CUDL2001"
