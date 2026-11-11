"""Portable, deterministic numeric TIME evaluator (experimental v1 subset).

The evaluator is independent of browser/native timers. Hosts provide a time
position and consume the resulting target values; rendering and frame delivery
remain adapter responsibilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import math
import re

from .bundle import ApplicationBundle
from .diagnostics import Diagnostic, Severity
from .parser import Node

_TIME_VALUE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)(ms|s|min)$", re.IGNORECASE)
_NUMBER = re.compile(r"^-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$")
_MODES = {"once", "loop", "ping-pong", "hold"}
_EASINGS = {"linear", "in", "out", "in-out", "in-cubic", "out-cubic", "in-out-cubic", "step", "spring"}


class TimeCompileError(ValueError):
    """Raised when a requested timeline cannot be compiled safely."""


def parse_time_us(value: str) -> int:
    """Parse a duration into integer microseconds without float drift."""
    match = _TIME_VALUE.fullmatch(value.strip())
    if not match:
        raise TimeCompileError(
            f"Invalid time value {value!r}; use a value with ms, s or min."
        )
    amount = Decimal(match.group(1))
    unit = match.group(2).casefold()
    factor = {"ms": Decimal(1000), "s": Decimal(1_000_000), "min": Decimal(60_000_000)}[unit]
    micros = amount * factor
    if micros != micros.to_integral_value():
        raise TimeCompileError("Time precision cannot be represented in whole microseconds.")
    return int(micros)


def _number(value: str) -> float:
    raw = value.strip()
    if not _NUMBER.fullmatch(raw):
        raise TimeCompileError(f"Only finite numeric keyframe values are supported in TIME v1: {value!r}.")
    result = float(raw)
    if not math.isfinite(result):
        raise TimeCompileError("Keyframe values must be finite.")
    return result


@dataclass(frozen=True, slots=True)
class Keyframe:
    at_us: int
    value: float


@dataclass(frozen=True, slots=True)
class Track:
    target: str
    start_us: int
    keyframes: tuple[Keyframe, ...]
    easing: str = "linear"

    @property
    def end_us(self) -> int:
        return self.start_us + self.keyframes[-1].at_us


@dataclass(frozen=True, slots=True)
class Scene:
    name: str
    at_us: int
    duration_us: int
    tracks: tuple[Track, ...]

    @property
    def end_us(self) -> int:
        return self.at_us + self.duration_us


@dataclass(frozen=True, slots=True)
class Timeline:
    name: str
    duration_us: int
    mode: str
    clock: str
    scenes: tuple[Scene, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "duration_us": self.duration_us,
            "mode": self.mode,
            "clock": self.clock,
            "scenes": [
                {
                    "name": scene.name,
                    "at_us": scene.at_us,
                    "duration_us": scene.duration_us,
                    "tracks": [
                        {
                            "target": track.target,
                            "start_us": track.start_us,
                            "easing": track.easing,
                            "keyframes": [
                                {"at_us": frame.at_us, "value": frame.value}
                                for frame in track.keyframes
                            ],
                        }
                        for track in scene.tracks
                    ],
                }
                for scene in self.scenes
            ],
        }

    def evaluate(self, position_ms: int | float) -> dict[str, float]:
        """Evaluate all numeric tracks at a timeline position in milliseconds."""
        position = Decimal(str(position_ms)) * Decimal(1000)
        if not position.is_finite():
            raise ValueError("Timeline position must be finite.")
        if position != position.to_integral_value():
            raise ValueError("Timeline position must resolve to whole microseconds.")
        time_us = max(0, int(position))
        if self.mode == "loop" and self.duration_us:
            time_us %= self.duration_us
        elif self.mode == "ping-pong" and self.duration_us:
            cycle = self.duration_us * 2
            time_us %= cycle
            if time_us > self.duration_us:
                time_us = cycle - time_us
        else:
            time_us = min(max(time_us, 0), self.duration_us)

        values: dict[str, float] = {}
        for scene in self.scenes:
            if time_us < scene.at_us:
                continue
            local_scene_us = min(time_us - scene.at_us, scene.duration_us)
            for track in scene.tracks:
                local_track_us = local_scene_us - track.start_us
                values[track.target] = _evaluate_track(track, local_track_us)
        return values


@dataclass(slots=True)
class TimeCompileResult:
    timelines: dict[str, Timeline]
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "timelines": {name: timeline.to_dict() for name, timeline in self.timelines.items()},
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _child(node: Node, kind: str) -> Node | None:
    matches = [item for item in node.children if item.kind.casefold() == kind]
    return matches[0] if matches else None


def _field_value(node: Node, kind: str, default: str | None = None) -> str | None:
    matches = [item for item in node.children if item.kind.casefold() == kind]
    if len(matches) > 1:
        raise TimeCompileError(f"The {kind!r} field may appear only once.")
    if not matches:
        return default
    return matches[0].value.strip()


def _reject_unknown_children(node: Node, allowed: set[str], owner: str) -> None:
    unexpected = [
        child for child in node.children
        if child.kind.casefold() not in allowed
    ]
    if unexpected:
        names = ", ".join(repr(item.kind) for item in unexpected)
        raise TimeCompileError(f"Unexpected declaration(s) inside {owner}: {names}.")


def _compile_track(node: Node, scene_duration_us: int) -> Track:
    _reject_unknown_children(node, {"start", "ease", "from", "to", "duration", "key"}, "track")
    target = node.value.strip()
    if not target or any(not part for part in target.split(".")):
        raise TimeCompileError("A track needs a dotted target path, for example card.opacity.")
    start_raw = _field_value(node, "start", "0ms")
    assert start_raw is not None
    start_us = parse_time_us(start_raw)
    if start_us > scene_duration_us:
        raise TimeCompileError(f"Track {target!r} starts after its scene ends.")

    easing = (_field_value(node, "ease", "linear") or "linear").casefold()
    if easing not in _EASINGS:
        raise TimeCompileError(f"Unsupported easing {easing!r} in TIME v1.")

    key_nodes = [item for item in node.children if item.kind.casefold() == "key"]
    if key_nodes:
        if _child(node, "from") or _child(node, "to") or _child(node, "duration"):
            raise TimeCompileError("Use explicit keyframes alone, or from/to shorthand with duration.")
        frames: list[Keyframe] = []
        for item in key_nodes:
            pieces = item.value.strip().split(maxsplit=1)
            if len(pieces) != 2:
                raise TimeCompileError("A keyframe must contain a time and a numeric value.")
            frames.append(Keyframe(parse_time_us(pieces[0]), _number(pieces[1])))
        if len(frames) < 2:
            raise TimeCompileError("An explicit track needs at least two keyframes.")
        if any(right.at_us <= left.at_us for left, right in zip(frames, frames[1:])):
            raise TimeCompileError("Keyframe times must be strictly increasing.")
    else:
        from_raw = _field_value(node, "from")
        to_raw = _field_value(node, "to")
        duration_raw = _field_value(node, "duration")
        if from_raw is None or to_raw is None or duration_raw is None:
            raise TimeCompileError("A track needs two keyframes or from, to and duration.")
        duration_us = parse_time_us(duration_raw)
        if duration_us <= 0:
            raise TimeCompileError("Track duration must be greater than zero.")
        frames = [Keyframe(0, _number(from_raw)), Keyframe(duration_us, _number(to_raw))]

    if start_us + frames[-1].at_us > scene_duration_us:
        raise TimeCompileError(f"Track {target!r} extends beyond its scene duration.")
    return Track(target=target, start_us=start_us, keyframes=tuple(frames), easing=easing)


def _compile_scene(node: Node) -> Scene:
    _reject_unknown_children(node, {"at", "duration", "track"}, "scene")
    name = node.value.strip()
    if not name:
        raise TimeCompileError("A scene must have a name.")
    at_raw = _field_value(node, "at", "0ms")
    duration_raw = _field_value(node, "duration")
    assert at_raw is not None
    if duration_raw is None:
        raise TimeCompileError(f"Scene {name!r} is missing its duration.")
    at_us = parse_time_us(at_raw)
    duration_us = parse_time_us(duration_raw)
    if duration_us <= 0:
        raise TimeCompileError(f"Scene {name!r} duration must be greater than zero.")
    tracks = tuple(
        _compile_track(item, duration_us)
        for item in node.children
        if item.kind.casefold() == "track"
    )
    return Scene(name=name, at_us=at_us, duration_us=duration_us, tracks=tracks)


def compile_time(bundle: ApplicationBundle) -> TimeCompileResult:
    """Compile TIME section declarations to immutable timeline models."""
    diagnostics: list[Diagnostic] = []
    timelines: dict[str, Timeline] = {}
    section = bundle.sections.get("time", [])
    for node in section:
        if node.kind.casefold() != "timeline":
            diagnostics.append(Diagnostic(
                code="CUDL3001",
                message=f"Unexpected TIME declaration {node.kind!r}; expected timeline.",
                severity=Severity.ERROR,
                line=node.line,
                source=bundle.source,
                suggestion="Declare time-based behavior inside a timeline block.",
            ))
            continue
        name = node.value.strip()
        try:
            _reject_unknown_children(node, {"duration", "mode", "clock", "scene"}, "timeline")
            if not name:
                raise TimeCompileError("A timeline must have a name.")
            key = name.casefold()
            if key in timelines:
                raise TimeCompileError(f"Timeline {name!r} is declared more than once.")
            duration_raw = _field_value(node, "duration")
            if duration_raw is None:
                raise TimeCompileError(f"Timeline {name!r} is missing its duration.")
            duration_us = parse_time_us(duration_raw)
            if duration_us <= 0:
                raise TimeCompileError("Timeline duration must be greater than zero.")
            mode = (_field_value(node, "mode", "once") or "once").casefold()
            if mode not in _MODES:
                raise TimeCompileError(f"Unsupported playback mode {mode!r}.")
            clock = (_field_value(node, "clock", "relative") or "relative").casefold()
            if clock not in {"relative", "monotonic"}:
                raise TimeCompileError(f"Unsupported clock {clock!r}; use relative or monotonic.")
            scenes = tuple(
                _compile_scene(item)
                for item in node.children
                if item.kind.casefold() == "scene"
            )
            if not scenes:
                raise TimeCompileError(f"Timeline {name!r} must contain at least one scene.")
            scene_names: set[str] = set()
            for scene in scenes:
                scene_key = scene.name.casefold()
                if scene_key in scene_names:
                    raise TimeCompileError(f"Scene {scene.name!r} is declared more than once.")
                scene_names.add(scene_key)
                if scene.end_us > duration_us:
                    raise TimeCompileError(f"Scene {scene.name!r} extends beyond timeline {name!r}.")
            timelines[key] = Timeline(
                name=name,
                duration_us=duration_us,
                mode=mode,
                clock=clock,
                scenes=scenes,
            )
        except TimeCompileError as exc:
            diagnostics.append(Diagnostic(
                code="CUDL3002",
                message=str(exc),
                severity=Severity.ERROR,
                line=node.line,
                source=bundle.source,
                suggestion="Check duration units, scene bounds, track keyframes and easing names.",
            ))
    return TimeCompileResult(timelines=timelines, diagnostics=diagnostics)


def _ease(progress: float, name: str) -> float:
    if name == "linear":
        return progress
    if name == "step":
        return 0.0 if progress < 1.0 else 1.0
    if name == "spring":
        damping = 0.55
        frequency = 8.0
        damped = frequency * math.sqrt(1 - damping * damping)

        def response(t: float) -> float:
            return 1 - math.exp(-damping * frequency * t) * (
                math.cos(damped * t)
                + (damping * frequency / damped) * math.sin(damped * t)
            )

        return response(progress) / response(1.0)
    if name in {"in", "in-cubic"}:
        return progress ** (3 if name == "in-cubic" else 2)
    if name in {"out", "out-cubic"}:
        power = 3 if name == "out-cubic" else 2
        return 1 - (1 - progress) ** power
    if name in {"in-out", "in-out-cubic"}:
        power = 3 if name == "in-out-cubic" else 2
        if progress < 0.5:
            return (2 ** (power - 1)) * (progress ** power)
        return 1 - ((-2 * progress + 2) ** power) / 2
    raise ValueError(f"Unsupported easing {name!r}.")


def _evaluate_track(track: Track, local_time_us: int) -> float:
    frames = track.keyframes
    if local_time_us <= frames[0].at_us:
        return frames[0].value
    if local_time_us >= frames[-1].at_us:
        return frames[-1].value
    for left, right in zip(frames, frames[1:]):
        if left.at_us <= local_time_us <= right.at_us:
            progress = (local_time_us - left.at_us) / (right.at_us - left.at_us)
            eased = _ease(progress, track.easing)
            return left.value + (right.value - left.value) * eased
    return frames[-1].value
