from cudl import Severity, parse


def test_parses_nested_page_structure():
    result = parse(
        'page Home\n'
        '    header\n'
        '        title "Hello, CUDL"\n'
        '    content\n'
        '        text "Welcome"\n'
    )

    assert not result.has_errors
    page = result.document.nodes[0]
    assert (page.kind, page.value) == ("page", "Home")
    assert [node.kind for node in page.children] == ["header", "content"]
    assert page.children[0].children[0].value == '"Hello, CUDL"'


def test_reports_non_four_space_indentation():
    result = parse("page Home\n  title \"Bad indent\"\n")
    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1002"
    assert result.diagnostics[0].severity is Severity.ERROR


def test_reports_tabs_in_indentation():
    result = parse("page Home\n\ttitle \"Bad indent\"\n")
    assert result.has_errors
    assert result.diagnostics[0].code == "CUDL1001"


def test_ignores_blank_lines_and_comments():
    result = parse("# comment\n\npage Home\n    title \"Hi\"\n")
    assert not result.has_errors
    assert len(result.document.nodes) == 1
