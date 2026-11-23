import json
from pathlib import Path

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


def test_check_command_accepts_all_repository_examples(monkeypatch, capsys):
    root = Path(__file__).resolve().parent.parent / "examples"
    for name in ("hello.cudl", "hello-react-python.cudl", "five-part-welcome.cudl"):
        monkeypatch.setattr("sys.argv", ["cudl", "check", str(root / name)])
        assert main() == 0
        assert "OK:" in capsys.readouterr().out


def test_bundle_command_compiles_canonical_five_part_example(monkeypatch, capsys):
    source = Path(__file__).resolve().parent.parent / "examples" / "five-part-welcome.cudl"
    monkeypatch.setattr("sys.argv", ["cudl", "bundle", str(source)])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["application"]["type"] == "CUDLApplicationIR"
    assert payload["application"]["name"] == "MotionCard"
    assert "welcomeintro" in payload["time"]["timelines"]
