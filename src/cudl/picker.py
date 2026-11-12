"""Safe host-aware selection of CUDL native script blocks.

PICKER selects source nodes for declared host profiles. It does not execute
native code, resolve registries, or install dependencies.
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
    "web": frozenset({"javascript", "typescript"}),
    "node": frozenset({"javascript", "typescript"}),
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
                {"language": node.kind.casefold(), "line": node.line, "source": node.raw_source}
                for node in self.selected
            ],
            "excluded": [
                {"language": language, "line": line}
                for language, line in self.excluded
            ],
        }


def host_languages(host: str, extra_languages: Iterable[str] = ()) -> frozenset[str]:
    key = host.strip().casefold()
    if key not in _HOST_LANGUAGES:
        raise ValueError(f"Unknown CUDL host {host!r}; add a host profile or explicitly select a supported host.")
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
    """Select portable CUDL/JSON blocks and native blocks supported by a host."""
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


def filter_scripts_for_hosts(
    nodes: Iterable[Node],
    hosts: Iterable[str],
    extra_languages: dict[str, Iterable[str]] | None = None,
) -> dict[str, PickerSelection]:
    """Create independent deterministic selections from one CUDL SCRIPTS section."""
    source_nodes = tuple(nodes)
    extras = extra_languages or {}
    result: dict[str, PickerSelection] = {}
    for host in hosts:
        key = host.strip().casefold()
        if key in result:
            raise ValueError(f"Duplicate CUDL host target: {host!r}")
        result[key] = filter_scripts(source_nodes, key, extras.get(key, ()))
    return result
