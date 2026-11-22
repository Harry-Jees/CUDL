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


def test_parses_indentation_scoped_layout_and_custom_component_tags():
    result = parse(
        "KIT\n"
        "    component WelcomeCard\n"
        "        property heading\n"
        "        <column>\n"
        "            <title heading>\n"
        "PAGES\n"
        "    <page Home>\n"
        "        <WelcomeCard>\n"
        "            heading = Welcome to CUDL\n"
    )

    assert not result.has_errors
    kit, pages = result.document.nodes
    component = kit.children[0]
    assert (component.kind, component.value) == ("component", "WelcomeCard")
    assert component.children[1].kind == "column"
    assert component.children[1].children[0].value == "heading"
    page = pages.children[0]
    assert (page.kind, page.value) == ("page", "Home")
    assert page.children[0].kind == "welcomecard"
    assert page.children[0].children[0].value == "= Welcome to CUDL"


def test_rejects_explicit_closing_layout_tags():
    result = parse("PAGES\n    <page Home>\n    </page>\n")
    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1009"


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



def test_diagnostic_includes_source_span_and_line_context():
    result = parse("page Home\n  title Bad indent\n", source="sample.cudl")
    diagnostic = result.diagnostics[0]

    payload = diagnostic.to_dict()
    assert payload["source"] == "sample.cudl"
    assert payload["line"] == 2
    assert payload["column"] == 1
    assert payload["end_column"] == 3
    assert payload["line_text"] == "  title Bad indent"
    assert "sample.cudl:2:1: error CUDL1002" in diagnostic.format()
    assert "^^" in diagnostic.format()
    assert "help:" in diagnostic.format()


def test_diagnostic_span_points_at_invalid_hash_statement():
    result = parse("#name\n", source="variables.cudl")
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "CUDL1004"
    assert diagnostic.column == 1
    assert diagnostic.end_column == len("#name") + 1
    assert diagnostic.line_text == "#name"


def test_rejects_inline_tag_attributes_but_allows_quoted_equals_text():
    invalid = parse("PAGES\n    <button Start color=red>\n", source="button.cudl")
    diagnostic = invalid.diagnostics[0]
    assert diagnostic.code == "CUDL1009"
    assert diagnostic.source == "button.cudl"
    assert diagnostic.line == 2
    assert diagnostic.column == 5

    valid = parse('PAGES\n    <title "A = B">\n')
    assert not valid.has_errors
    assert valid.document.nodes[0].children[0].value == '"A = B"'


def test_rejects_malformed_function_names_and_missing_argument_separator():
    for statement in ("@", "@9start", "@start!", "@start#person"):
        result = parse(f"SCRIPTS\n    {statement}\n", source="functions.cudl")
        diagnostic = result.diagnostics[0]
        assert diagnostic.code == "CUDL1010"
        assert diagnostic.source == "functions.cudl"
        assert diagnostic.line == 2
        assert diagnostic.column == 5


def test_accepts_function_without_arguments_and_with_whitespace_separated_arguments():
    result = parse("SCRIPTS\n    @start\n    @greet #person\n")
    assert not result.has_errors
    assert [node.kind for node in result.document.nodes[0].children] == ["@start", "@greet"]
    assert result.document.nodes[0].children[1].value == "#person"


def test_malformed_function_diagnostic_is_stable():
    first = parse("SCRIPTS\n    @bad!\n", source="stable.cudl").diagnostics[0].to_dict()
    second = parse("SCRIPTS\n    @bad!\n", source="stable.cudl").diagnostics[0].to_dict()
    assert first == second


def test_parses_quoted_tag_value_with_inner_delimiter_and_comment_marker():
    result = parse(
        'PAGES\n'
        '    <page Home>\n'
        '        <title "Welcome > CUDL ##">\n',
    )
    assert not result.has_errors
    page = result.document.nodes[0].children[0]
    assert page.children[0].value == '"Welcome > CUDL ##"'
