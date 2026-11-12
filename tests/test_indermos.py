import pytest

from cudl.indermos import analyze_project


def test_detects_react_python_and_android_stacks_from_manifests():
    result = analyze_project({
        "web/package.json": '{"dependencies":{"react":"^19.0.0","zod":"^4.0.0"}}',
        "api/requirements.txt": "fastapi==0.115.0\nuvicorn>=0.30\n",
        "android/src/main/AndroidManifest.xml": "<manifest />",
    })
    names = {item.name for item in result.stacks}
    assert {"react", "node", "python", "android"} <= names
    assert any(item.name == "fastapi" and item.version == "0.115.0" for item in result.dependencies)
    assert any(item.name == "zod" and item.ecosystem == "npm" for item in result.dependencies)


def test_explicit_cudl_guide_targets_take_priority():
    result = analyze_project({
        "app.cudl": (
            "GUIDE\n"
            "    targets = [react, python]\n"
            "PAGES\n"
            "    page Home\n"
        )
    })
    assert {item.name for item in result.stacks} == {"react", "python"}
    assert all(item.confidence == 1.0 for item in result.stacks)


def test_detects_conflicting_declared_versions_without_installing():
    result = analyze_project({
        "requirements.txt": "httpx==0.25.0\nhttpx==0.27.0\n"
    })
    assert any("Conflicting declared versions" in item for item in result.warnings)


def test_rejects_paths_outside_supplied_project_root():
    with pytest.raises(ValueError, match="escapes"):
        analyze_project({"../secrets.txt": "not read"})
