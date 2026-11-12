"""Safe host-aware selection of CUDL native script blocks.

PICKER selects source nodes for a declared host. It does not execute native
code, resolve packages, or claim that a runtime is installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .parser import Node

_LANGUAGE_ALIASES = {
    "js": "javascript", "javascript": "javascript",
    "ts": "typescript", "typescript": "typescript",
    "py": "python", "python": "python",
    "kt": "kotlin", "kotlin": "kotlin",
    "swift": "swift", "java": "java", "c": "c", "cpp": "cpp",
    "rust": "rust", "go": "go", "json": "json", "script": "cudl",
}
_HOST_LANGUAGES = {
    "react": frozenset({"javascript", "typescript"}),
    "react-native": frozenset({"javascript", "typescript"}),
    "python": frozenset({"python"}),
    "android": frozenset({"kotlin", "java"}),
    "ios": frozenset({"swift"}),
}


@dataclass(frozen=True, slots=True)
class PickerSelection:
    host: str
    selected: tuple[Node, ...]
    excluded: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLPickerSelection",
            "version": 1,
            "host": self.host,
            "selected": [
                {"language": node.kind.casefold(), "line": node.line}
                for node in self.selected
            ],
            "excluded": [
                {"language": language, "line": line}
                for language, line in self.excluded
            ],
        }


def host_languages(host: str, extra_languages: Iterable[str] = ()) -> frozenset[str]:
    """Resolve a known host profile plus explicitly declared native languages."""
    key = host.strip().casefold()
    if key not in _HOST_LANGUAGES:
        raise ValueError(
            f"Unknown CUDL host {host!r}; provide explicit extra_languages "
            "for a supported host or add a host profile."
        )
    extras = {
        _LANGUAGE_ALIASES.get(item.strip().casefold(), item.strip().casefold())
        for item in extra_languages
    }
    return _HOST_LANGUAGES[key] | frozenset(extras)


def filter_scripts(
    nodes: Iterable[Node],
    host: str,
    extra_languages: Iterable[str] = (),
) -> PickerSelection:
    """Select CUDL and compatible native blocks for a declared host.

    Portable CUDL script blocks and JSON data blocks are always included.
    JSON is data, not executable code. Unknown blocks are ignored rather than
    executed or guessed.
    """
    supported = host_languages(host, extra_languages)
    selected: list[Node] = []
    excluded: list[tuple[str, int]] = []
    for node in nodes:
        language = _LANGUAGE_ALIASES.get(node.kind.casefold())
        if language is None:
            continue
        if language in {"cudl", "json"} or language in supported:
            selected.append(node)
        else:
            excluded.append((node.kind.casefold(), node.line))
    return PickerSelection(host.casefold(), tuple(selected), tuple(excluded))
