from cudl import lower, parse


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
