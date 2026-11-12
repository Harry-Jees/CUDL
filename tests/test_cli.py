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



def test_analyze_command_reports_detected_stacks_and_dependencies(tmp_path, monkeypatch, capsys):
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"react":"^19.0.0"}}', encoding="utf-8"
    )
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.0\n", encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["cudl", "analyze", str(tmp_path)])

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert {"react", "node", "python"} <= {item["name"] for item in payload["stacks"]}
    assert any(item["name"] == "fastapi" for item in payload["dependencies"])
