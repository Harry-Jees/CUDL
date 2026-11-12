from cudl.parser import parse
from cudl.ir import lower
from cudl.picker import filter_scripts, filter_scripts_for_hosts


def _script_nodes(source):
    result = parse(source)
    assert not result.has_errors
    scripts = next(node for node in result.document.nodes if node.kind == "scripts")
    return scripts.children


def test_react_picker_keeps_javascript_and_json_but_excludes_python():
    selection = filter_scripts(
        _script_nodes(
            "SCRIPTS\n"
            "    script\n"
            "        #ready = true\n"
            "    javascript\n"
            "        const greeting = 'hello'\n"
            "    python\n"
            "        print('hello')\n"
            "    json\n"
            "        {name: Hello}\n"
        ),
        "react",
    )
    assert [node.kind for node in selection.selected] == ["script", "javascript", "json"]
    assert selection.excluded == (("python", 6),)


def test_python_picker_selects_python_and_keeps_portable_blocks():
    selection = filter_scripts(_script_nodes(
        "SCRIPTS\n"
        "    SCRIPT\n"
        "    Python\n"
        "    JS\n"
        "    JSON\n"
    ), "python")
    assert [node.kind for node in selection.selected] == ["script", "python", "json"]
    assert [item[0] for item in selection.excluded] == ["js"]


def test_picker_supports_explicit_extra_host_language():
    selection = filter_scripts(_script_nodes(
        "SCRIPTS\n"
        "    rust\n"
        "    python\n"
    ), "python", extra_languages=["rust"])
    assert [node.kind for node in selection.selected] == ["rust", "python"]


def test_unknown_host_is_not_guessed():
    import pytest

    with pytest.raises(ValueError, match="Unknown CUDL host"):
        filter_scripts([], "mystery")


def test_native_blocks_preserve_source_without_parsing_host_syntax():
    source = (
        "SCRIPTS\n"
        "    python\n"
        "        def greeting():\n"
        "            return 'hello'\n"
        "    javascript\n"
        "        export const greeting = () => 'hello';\n"
    )
    nodes = _script_nodes(source)
    assert nodes[0].raw_source == "def greeting():\n    return 'hello'"
    assert nodes[1].raw_source == "export const greeting = () => 'hello';"
    assert nodes[0].children == []


def test_native_source_survives_lowering_into_ir():
    parsed = parse(
        "SCRIPTS\n"
        "    python\n"
        "        print('hello')\n"
    )
    ir = lower(parsed.document).to_dict()
    assert ir["nodes"][0]["children"][0]["raw_source"] == "print('hello')"


def test_multi_host_picker_creates_independent_react_and_python_selections():
    nodes = _script_nodes(
        "SCRIPTS\n"
        "    javascript\n"
        "        const web = true\n"
        "    python\n"
        "        print('native')\n"
        "    json\n"
        "        { }\n"
    )
    selections = filter_scripts_for_hosts(nodes, ["react", "python"])
    assert [node.kind for node in selections["react"].selected] == ["javascript", "json"]
    assert [node.kind for node in selections["python"].selected] == ["python", "json"]
