import copy

import pytest

from cudl import IRDocument, IRValidationError, lower, parse


def test_lowers_page_tree_to_versioned_ir():
    parsed = parse(
        'page Home\n'
        '    header\n'
        '        title "Welcome"\n'
        '    content\n'
        '        button "Continue"\n',
        source="pages/home.cudl",
    )
    ir = lower(parsed.document).to_dict()

    assert ir["type"] == "CUDLIR"
    assert ir["version"] == 1
    assert ir["source"] == "pages/home.cudl"
    page = ir["nodes"][0]
    assert page["category"] == "layout"
    assert page["name"] == "page"
    assert page["children"][0]["category"] == "layout"
    assert page["children"][0]["children"][0]["category"] == "element"


def test_unknown_custom_component_is_preserved():
    parsed = parse("ProfileCard\n    text \"Hello\"\n")
    node = lower(parsed.document).nodes[0]
    assert node.name == "profilecard"
    assert node.category == "generic"
    assert node.children[0].name == "text"


def test_ir_serialization_is_deterministic():
    document = parse("page Home\n    text \"Hi\"\n").document
    assert lower(document).to_dict() == lower(document).to_dict()


def test_script_functions_are_declarations_not_components():
    parsed = parse(
        "script\n"
        "    @greet #person\n"
        "        print Hello #person\n"
        "    @greet Harry\n"
    )
    ir = lower(parsed.document)
    script = ir.nodes[0]
    assert script.category == "declaration"
    assert script.children[0].kind == "@greet"
    assert script.children[0].category == "declaration"
    assert script.children[1].kind == "@greet"
    assert script.children[1].category == "generic"


def test_ir_round_trip_preserves_order_values_and_native_source():
    parsed = parse(
        "script\n"
        "    #items = [alpha, beta]\n"
        "    javascript\n"
        "        console.log(\"safe\")\n"
        "    @greet #person\n"
        "        print Hello #person\n",
        source="scripts/main.cudl",
    )
    assert not parsed.has_errors

    original = lower(parsed.document)
    restored = IRDocument.from_dict(original.to_dict())

    assert restored.to_dict() == original.to_dict()
    children = restored.nodes[0].children
    assert [child.kind for child in children] == ["variable", "javascript", "@greet"]
    assert children[0].value == "#items = [alpha, beta]"
    assert children[1].raw_source == 'console.log("safe")'
    assert children[2].category == "declaration"


def test_ir_deserializer_rejects_unknown_versions_and_invalid_provenance():
    payload = lower(parse("page Home").document).to_dict()
    unsupported = copy.deepcopy(payload)
    unsupported["version"] = 2
    with pytest.raises(IRValidationError, match="Unsupported CUDL IR version"):
        IRDocument.from_dict(unsupported)

    invalid_line = copy.deepcopy(payload)
    invalid_line["nodes"][0]["source"]["line"] = 0
    with pytest.raises(IRValidationError, match="positive integer"):
        IRDocument.from_dict(invalid_line)


def test_ir_deserializer_enforces_node_and_nesting_limits(monkeypatch):
    payload = lower(parse("page Home\n    header\n        text Hello").document).to_dict()

    monkeypatch.setattr("cudl.ir.MAX_NODES", 2)
    with pytest.raises(IRValidationError, match="node safety limit"):
        IRDocument.from_dict(payload)

    monkeypatch.setattr("cudl.ir.MAX_NODES", 50_000)
    monkeypatch.setattr("cudl.ir.MAX_NESTING_LEVEL", 1)
    with pytest.raises(IRValidationError, match="nesting exceeds"):
        IRDocument.from_dict(payload)
