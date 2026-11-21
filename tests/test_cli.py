import json

from cudl.cli import main


def test_bundle_command_emits_application_and_time_ir(tmp_path, monkeypatch, capsys):
    source = tmp_path / "app.cudl"
    source.write_text(
        "bundle Demo\n"
        "    GUIDE\n"
        "        name = Demo\n"
        "    PAGES\n"
        "        page Home\n"
        "    TIME\n"
        "        timeline Intro\n"
        "            duration 1000ms\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 1000ms\n"
        "                track card.opacity\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 1000ms\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["cudl", "bundle", str(source)])

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["application"]["type"] == "CUDLApplicationIR"
    assert "intro" in payload["time"]["timelines"]


def test_bundle_command_reports_invalid_time(tmp_path, monkeypatch, capsys):
    source = tmp_path / "invalid.cudl"
    source.write_text(
        "GUIDE\n"
        "    name = Demo\n"
        "TIME\n"
        "    timeline Intro\n"
        "        duration 1000\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["cudl", "bundle", str(source)])

    assert main() == 1
    assert "CUDL3002" in capsys.readouterr().err



def test_routes_command_selects_android_phone_implementation(tmp_path, monkeypatch, capsys):
    source = tmp_path / "app.cudl"
    source.write_text(
        "KIT\n"
        "    component Navigation\n"
        "        route = android\n"
        "            device = phone\n"
        "            use = AndroidPhoneNavigation\n"
        "        route = default\n"
        "            use = ResponsiveNavigation\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["cudl", "routes", str(source), "--component", "Navigation",
         "--platform", "android", "--device", "phone"],
    )
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["implementation"] == "AndroidPhoneNavigation"


def test_check_reports_invalid_utf8_without_traceback(tmp_path, monkeypatch, capsys):
    source = tmp_path / "invalid.cudl"
    source.write_bytes(b"\xff")
    monkeypatch.setattr("sys.argv", ["cudl", "check", str(source)])

    assert main() == 2
    captured = capsys.readouterr()
    assert "cannot read" in captured.err
    assert captured.out == ""


def test_graph_reports_invalid_module_encoding(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    project.mkdir()
    (project / "entry.cudl").write_text("page Home\n", encoding="utf-8")
    (project / "broken.cudl").write_bytes(b"\\xff")
    monkeypatch.setattr("sys.argv", ["cudl", "graph", str(project), "entry.cudl"])

    assert main() == 2
    captured = capsys.readouterr()
    assert "cannot read CUDL module" in captured.err
    assert captured.out == ""
