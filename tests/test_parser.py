from cudl import Severity, parse


def test_parses_nested_page_structure_without_text_quotes():
    result = parse(
        "page Home\n"
        "    header\n"
        "        title Hello CUDL\n"
        "    content\n"
        "        text Welcome\n"
    )

    assert not result.has_errors
    page = result.document.nodes[0]
    assert (page.kind, page.value) == ("page", "Home")
    assert [node.kind for node in page.children] == ["header", "content"]
    assert page.children[0].children[0].value == "Hello CUDL"


def test_preserves_hash_variables_and_at_functions():
    result = parse(
        "script\n"
        "    #name = Harry\n"
        "    @greet #person\n"
        "        print Hello #person\n"
        "    @greet #name\n"
    )

    assert not result.has_errors
    script = result.document.nodes[0]
    assert script.children[0].kind == "variable"
    assert script.children[0].value == "#name = Harry"
    function = script.children[1]
    assert (function.kind, function.value) == ("@greet", "#person")
    assert script.children[2].kind == "@greet"
    assert script.children[2].value == "#name"
    assert not script.children[2].children


def test_reports_non_four_space_indentation():
    result = parse("page Home\n  title Bad indent\n")
    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1002"
    assert result.diagnostics[0].severity is Severity.ERROR


def test_reports_tabs_in_indentation():
    result = parse("page Home\n\ttitle Bad indent\n")
    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1001"


def test_ignores_double_hash_comments_but_keeps_hash_variables():
    result = parse("## comment\n\n#name = Harry\npage Home ## inline comment\n")
    assert not result.has_errors
    assert len(result.document.nodes) == 2
    assert result.document.nodes[0].kind == "variable"


def test_inline_comments_are_removed_without_changing_quoted_hashes():
    result = parse('page Home ## comment\n    title "Keep ## inside text"\n')
    assert not result.has_errors
    page = result.document.nodes[0]
    assert page.value == "Home"
    assert page.children[0].value == '"Keep ## inside text"'


def test_rejects_invalid_hash_variable_statements():
    for source in ("# = value\n", "#9name = value\n", "#name\n", "#name =\n"):
        result = parse(source)
        assert result.has_errors
        assert result.diagnostics[0].code == "CUDL1004"



def test_parser_rejects_source_over_resource_limit(monkeypatch):
    import cudl.parser as parser_module

    monkeypatch.setattr(parser_module, "MAX_SOURCE_CHARACTERS", 4)
    result = parse("page Home")

    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1005"
    assert result.document.nodes == []


def test_parser_rejects_oversized_lines(monkeypatch):
    import cudl.parser as parser_module

    monkeypatch.setattr(parser_module, "MAX_LINE_CHARACTERS", 8)
    result = parse("page TooLong")

    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1006"


def test_parser_rejects_excessive_nesting(monkeypatch):
    import cudl.parser as parser_module

    monkeypatch.setattr(parser_module, "MAX_NESTING_LEVEL", 1)
    result = parse("page Home\n    title Child\n        text TooDeep")

    assert result.has_errors
    assert any(item.code == "CUDL1007" for item in result.diagnostics)


def test_parser_stops_after_node_limit(monkeypatch):
    import cudl.parser as parser_module

    monkeypatch.setattr(parser_module, "MAX_NODES", 2)
    result = parse("first\nsecond\nthird")

    assert result.has_errors
    assert len(result.document.nodes) == 2
    assert result.diagnostics[-1].code == "CUDL1008"
