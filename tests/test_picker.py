import json

from cudl import filter_scripts, filter_scripts_for_hosts, host_languages, parse_bundle
from cudl.cli import main


def _scripts():
    source = (
        "GUIDE\n"
        "    name = PickerDemo\n"
        "SCRIPTS\n"
        "    javascript\n"
        "        console.log('web');\n"
        "    python\n"
        "        print('python host');\n"
        "    json\n"
        "        {\"version\": 1}\n"
        "    kotlin\n"
        "        println(\"android host\")\n"
    )
    parsed = parse_bundle(source)
    assert not parsed.has_errors
    return parsed.bundle.sections["scripts"]


def test_picker_selects_host_native_blocks_and_portable_json():
    selection = filter_scripts(_scripts(), "react")

    assert [node.kind for node in selection.selected] == ["javascript", "json"]
    assert [language for language, _ in selection.excluded] == ["python", "kotlin"]
    assert selection.selected[0].raw_source == "console.log('web');"
    assert selection.to_dict()["selected"][0]["source"] == "console.log('web');"


def test_picker_supports_language_aliases_and_explicit_host_extensions():
    assert "python" in host_languages("react", ["py"])
    selection = filter_scripts(_scripts(), "react", ["py"])
    assert [node.kind for node in selection.selected] == ["javascript", "python", "json"]
    assert [language for language, _ in selection.excluded] == ["kotlin"]


def test_picker_creates_independent_host_selections():
    results = filter_scripts_for_hosts(_scripts(), ["react", "python"])
    assert [node.kind for node in results["react"].selected] == ["javascript", "json"]
    assert [node.kind for node in results["python"].selected] == ["python", "json"]


def test_picker_rejects_unknown_and_duplicate_hosts():
    try:
        host_languages("unknown-host")
    except ValueError as exc:
        assert "Unknown CUDL host" in str(exc)
    else:
        raise AssertionError("unknown hosts must fail closed")

    try:
        filter_scripts_for_hosts(_scripts(), ["React", "react"])
    except ValueError as exc:
        assert "Duplicate CUDL host" in str(exc)
    else:
        raise AssertionError("duplicate normalized hosts must fail")


def test_picker_cli_reports_selected_and_excluded_blocks(tmp_path, monkeypatch, capsys):
    source = tmp_path / "picker.cudl"
    source.write_text(
        "GUIDE\n"
        "    name = PickerDemo\n"
        "SCRIPTS\n"
        "    javascript\n"
        "        console.log('web');\n"
        "    python\n"
        "        print('python host');\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["cudl", "picker", str(source), "--host", "react"])

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "CUDLPickerSelection"
    assert payload["host"] == "react"
    assert payload["selected"] == [
        {"language": "javascript", "line": 4, "source": "console.log('web');"}
    ]
    assert payload["excluded"] == [{"language": "python", "line": 6}]


def test_picker_cli_fails_closed_for_unknown_host(tmp_path, monkeypatch, capsys):
    source = tmp_path / "picker.cudl"
    source.write_text("SCRIPTS\n    javascript\n        console.log('x');\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["cudl", "picker", str(source), "--host", "unknown-host"])

    assert main() == 2
    assert "CUDL7001" in capsys.readouterr().err



def test_picker_preserves_unknown_languages_as_unsupported():
    parsed = parse_bundle(
        "SCRIPTS\n"
        "    brainfuck\n"
        "        +++[>+++<-]\n"
    )
    assert not parsed.has_errors

    selection = filter_scripts(parsed.bundle.sections["scripts"], "react")

    assert selection.selected == ()
    assert selection.unsupported == (("brainfuck", 2),)
    assert selection.to_dict()["unsupported"] == [
        {"language": "brainfuck", "line": 2}
    ]


def test_picker_cli_builds_independent_multi_host_previews_and_reports_unknowns(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "multi-host.cudl"
    source.write_text(
        "GUIDE\n"
        "    name = MultiHost\n"
        "SCRIPTS\n"
        "    javascript\n"
        "        console.log('web');\n"
        "    python\n"
        "        print('python host');\n"
        "    brainfuck\n"
        "        +++[>+++<-]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["cudl", "picker", str(source), "--host", "react", "--host", "python"],
    )

    assert main() == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "CUDL7002" in captured.err

    assert payload["type"] == "CUDLMultiHostPickerSelection"
    assert [item["host"] for item in payload["selections"]] == ["react", "python"]
    assert [item["language"] for item in payload["selections"][0]["selected"]] == ["javascript"]
    assert [item["language"] for item in payload["selections"][1]["selected"]] == ["python"]
    assert payload["selections"][0]["unsupported"][0]["language"] == "brainfuck"


def test_picker_cli_reports_unsupported_language_warning(tmp_path, monkeypatch, capsys):
    source = tmp_path / "unknown.cudl"
    source.write_text(
        "SCRIPTS\n"
        "    brainfuck\n"
        "        +++[>+++<-]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv", ["cudl", "picker", str(source), "--host", "react"]
    )

    assert main() == 0
    captured = capsys.readouterr()
    assert "CUDL7002" in captured.err
    assert "brainfuck" in captured.err
