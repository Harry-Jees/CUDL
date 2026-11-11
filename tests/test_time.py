import pytest

from cudl import parse_bundle
from cudl.time import TimeCompileError, compile_time, parse_time_us


def _bundle(time_source):
    return parse_bundle(
        "bundle Demo\n"
        "    GUIDE\n"
        "        name Demo\n"
        "    TIME\n" + time_source
    ).bundle


def test_time_values_normalize_to_integer_microseconds():
    assert parse_time_us("250ms") == 250_000
    assert parse_time_us("1.5s") == 1_500_000
    assert parse_time_us("2min") == 120_000_000


@pytest.mark.parametrize("value", ["100", "1frame", "-1s", "1.0000001ms"])
def test_time_values_reject_ambiguous_or_unrepresentable_units(value):
    with pytest.raises(TimeCompileError):
        parse_time_us(value)


def test_compiles_and_evaluates_numeric_timeline_with_scene_offsets():
    bundle = _bundle(
        "        timeline Intro\n"
        "            duration 1500ms\n"
        "            mode once\n"
        "            scene Entrance\n"
        "                at 100ms\n"
        "                duration 1000ms\n"
        "                track card.opacity\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 700ms\n"
        "                    ease out-cubic\n"
    )
    result = compile_time(bundle)

    assert not result.has_errors
    timeline = result.timelines["intro"]
    assert timeline.evaluate(99) == {}
    assert timeline.evaluate(100)["card.opacity"] == 0
    assert timeline.evaluate(750)["card.opacity"] > 0.9
    assert timeline.evaluate(750)["card.opacity"] < 1
    assert timeline.evaluate(1500)["card.opacity"] == 1


def test_explicit_keyframes_are_interpolated_and_loop_mode_wraps():
    bundle = _bundle(
        "        timeline Pulse\n"
        "            duration 1000ms\n"
        "            mode loop\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 1000ms\n"
        "                track dot.scale\n"
        "                    key 0ms 1\n"
        "                    key 500ms 3\n"
        "                    key 1000ms 1\n"
        "                    ease linear\n"
    )
    result = compile_time(bundle)
    assert not result.has_errors
    timeline = result.timelines["pulse"]
    assert timeline.evaluate(250)["dot.scale"] == 2
    assert timeline.evaluate(1250)["dot.scale"] == 2


def test_invalid_track_bounds_and_easing_are_diagnostics():
    bundle = _bundle(
        "        timeline Broken\n"
        "            duration 500ms\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 500ms\n"
        "                track card.opacity\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 700ms\n"
        "                    ease elastic\n"
    )
    result = compile_time(bundle)
    assert result.has_errors
    assert any(item.code == "CUDL3002" for item in result.diagnostics)


def test_multiple_tracks_evaluate_independently():
    bundle = _bundle(
        "        timeline Intro\n"
        "            duration 1000ms\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 1000ms\n"
        "                track card.opacity\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 1000ms\n"
        "                track card.scale\n"
        "                    from 1\n"
        "                    to 2\n"
        "                    duration 500ms\n"
    )
    result = compile_time(bundle)
    assert not result.has_errors
    values = result.timelines["intro"].evaluate(500)
    assert values == {"card.opacity": 0.5, "card.scale": 2.0}

def test_spring_easing_is_supported_and_finishes_at_target():
    bundle = _bundle(
        "        timeline Spring\n"
        "            duration 1000ms\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 1000ms\n"
        "                track card.scale\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 1000ms\n"
        "                    ease spring\n"
    )
    result = compile_time(bundle)
    assert not result.has_errors
    timeline = result.timelines["spring"]
    assert timeline.evaluate(0)["card.scale"] == 0
    assert timeline.evaluate(1000)["card.scale"] == pytest.approx(1)


def test_time_compiler_rejects_unknown_and_duplicate_fields():
    bundle = _bundle(
        "        timeline Invalid\n"
        "            duration 1000ms\n"
        "            duration 1200ms\n"
        "            scene Main\n"
        "                at 0ms\n"
        "                duration 1000ms\n"
        "                track card.opacity\n"
        "                    from 0\n"
        "                    to 1\n"
        "                    duration 500ms\n"
        "                    typo value\n"
    )
    result = compile_time(bundle)
    assert result.has_errors
    assert any("only once" in item.message for item in result.diagnostics)
