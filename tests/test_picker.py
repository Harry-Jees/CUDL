from cudl.parser import parse
from cudl.picker import filter_scripts


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
    assert selection.excluded == (("python", 5),)


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
