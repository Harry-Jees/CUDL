from cudl import lower_bundle, parse_bundle


def test_parses_all_five_sections_inside_named_bundle():
    result = parse_bundle(
        "bundle WelcomeApp\n"
        "    GUIDE\n"
        "        name = WelcomeApp\n"
        "    KIT\n"
        "        component Card\n"
        "    PAGES\n"
        "        page Home\n"
        "    SCRIPTS\n"
        "        #ready = true\n"
        "    TIME\n"
        "        timeline Intro\n"
        "            duration 1s\n",
        source="app.cudl",
    )

    assert not result.has_errors
    assert result.bundle.name == "WelcomeApp"
    assert tuple(result.bundle.sections) == ("guide", "kit", "pages", "scripts", "time")
    assert result.bundle.source == "app.cudl"


def test_allows_omitted_sections_and_direct_root_sections():
    result = parse_bundle(
        "GUIDE\n"
        "    name = SmallApp\n"
        "PAGES\n"
        "    page Home\n"
    )

    assert not result.has_errors
    assert set(result.bundle.sections) == {"guide", "pages"}


def test_rejects_duplicate_sections():
    result = parse_bundle(
        "GUIDE\n"
        "    name = First\n"
        "GUIDE\n"
        "    name = Second\n"
    )

    assert result.has_errors
    assert any(item.code == "CUDL2004" for item in result.diagnostics)


def test_allows_sections_in_any_order_and_normalizes_ir_order():
    result = parse_bundle(
        "pAgEs\n"
        "    page Home\n"
        "gUiDe\n"
        "    name = App\n"
        "sCrIpTs\n"
        "    #ready = true\n"
        "kIt\n"
        "    theme = warm\n"
        "tImE\n"
        "    timeline Intro\n"
        "        duration 1s\n"
    )

    assert not result.has_errors
    assert tuple(result.bundle.sections) == ("pages", "guide", "scripts", "kit", "time")
    assert tuple(lower_bundle(result.bundle).sections) == ("pages", "guide", "scripts", "kit", "time")
    assert list(lower_bundle(result.bundle).to_dict()["sections"]) == [
        "guide", "kit", "pages", "scripts", "time"
    ]


def test_rejects_unknown_top_level_statements():
    result = parse_bundle("page Home\n")

    assert result.has_errors
    assert any(item.code == "CUDL2003" for item in result.diagnostics)


def test_bundle_wrapper_must_be_the_only_root_statement():
    result = parse_bundle(
        "bundle App\n"
        "    PAGES\n"
        "        page Home\n"
        "GUIDE\n"
        "    name = App\n"
    )

    assert result.has_errors
    assert any(item.code == "CUDL2002" for item in result.diagnostics)


def test_lower_bundle_emits_versioned_typed_section_ir():
    parsed = parse_bundle(
        "bundle WelcomeApp\n"
        "    GUIDE\n"
        "        name = WelcomeApp\n"
        "    PAGES\n"
        "        page Home\n"
        "            text Hello\n"
        "    TIME\n"
        "        timeline Intro\n"
        "            duration 1200ms\n"
    )
    assert not parsed.has_errors

    ir = lower_bundle(parsed.bundle).to_dict()

    assert ir["type"] == "CUDLApplicationIR"
    assert ir["version"] == 1
    assert ir["name"] == "WelcomeApp"
    assert list(ir["sections"]) == ["guide", "pages", "time"]
    assert ir["sections"]["pages"]["type"] == "CUDLIR"
    assert ir["sections"]["pages"]["nodes"][0]["name"] == "page"
    assert ir["sections"]["time"]["nodes"][0]["name"] == "timeline"


def test_empty_source_reports_missing_application_sections():
    result = parse_bundle("## only a comment\n")

    assert result.has_errors
    assert any(item.code == "CUDL2006" for item in result.diagnostics)

def test_reports_multiple_bundle_wrappers_without_crashing():
    result = parse_bundle(
        "bundle First\n"
        "    GUIDE\n"
        "        name = First\n"
        "bundle Second\n"
        "    PAGES\n"
        "        page Home\n"
    )

    assert result.has_errors
    assert any(item.code == "CUDL2001" for item in result.diagnostics)


def test_requires_equals_for_guide_and_kit_configuration():
    result = parse_bundle(
        "GUIDE\n"
        "    name App\n"
        "KIT\n"
        "    theme = warm\\n"
        "        background #ffffff\n"
    )
    assert result.has_errors
    assert sum(item.code == "CUDL2007" for item in result.diagnostics) == 2
