"""Read-only host stack and manifest dependency analysis for INDERMOS.

This module inspects caller-supplied project files only. It never accesses the
network, executes build scripts, installs packages, or reads outside the input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import posixpath
import re
from typing import Mapping

from .modules import resolve_project


@dataclass(frozen=True, slots=True)
class HostStack:
    name: str
    language: str
    manifest: str
    evidence: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class DeclaredDependency:
    ecosystem: str
    name: str
    version: str | None
    manifest: str


@dataclass(slots=True)
class StackAnalysis:
    stacks: list[HostStack] = field(default_factory=list)
    dependencies: list[DeclaredDependency] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    module_graph: dict[str, object] | None = None

    @property
    def primary(self) -> HostStack | None:
        return self.stacks[0] if self.stacks else None

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "CUDLStackAnalysis",
            "version": 1,
            "primary": self.primary.name if self.primary else None,
            "stacks": [
                {
                    "name": item.name,
                    "language": item.language,
                    "manifest": item.manifest,
                    "evidence": list(item.evidence),
                    "confidence": item.confidence,
                }
                for item in self.stacks
            ],
            "dependencies": [
                {
                    "ecosystem": item.ecosystem,
                    "name": item.name,
                    "version": item.version,
                    "manifest": item.manifest,
                }
                for item in self.dependencies
            ],
            "warnings": list(self.warnings),
            "module_graph": self.module_graph,
        }


def _normal_files(files: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for path, content in files.items():
        key = posixpath.normpath(path.replace("\\", "/"))
        if key in {"", ".", ".."} or key.startswith("../") or key.startswith("/"):
            raise ValueError(f"Project path escapes the supplied root: {path!r}")
        if key.startswith("./"):
            key = key[2:]
        normalized[key] = content
    return normalized

def _add_stack(found: dict[str, HostStack], stack: HostStack) -> None:
    current = found.get(stack.name)
    if current is None:
        found[stack.name] = stack
    else:
        found[stack.name] = HostStack(
            stack.name,
            stack.language,
            current.manifest,
            tuple(dict.fromkeys((*current.evidence, *stack.evidence))),
            min(1.0, current.confidence + stack.confidence * 0.15),
        )


def _package_json(path: str, content: str, found: dict[str, HostStack], deps: list[DeclaredDependency], warnings: list[str]) -> None:
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        warnings.append(f"{path}: invalid JSON manifest.")
        return
    if not isinstance(data, dict):
        warnings.append(f"{path}: package manifest root must be an object.")
        return
    sections = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
    names: set[str] = set()
    for section in sections:
        values = data.get(section, {})
        if isinstance(values, dict):
            for name, version in values.items():
                names.add(str(name))
                deps.append(DeclaredDependency("npm", str(name), str(version), path))
    if "react" in names:
        _add_stack(found, HostStack("react", "javascript", path, ("react dependency",), 0.98))
    if "react-native" in names:
        _add_stack(found, HostStack("react-native", "javascript", path, ("react-native dependency",), 0.99))
    _add_stack(found, HostStack("node", "javascript", path, ("package.json",), 0.85))


def _requirements(path: str, content: str, deps: list[DeclaredDependency]) -> None:
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*(?:(?:==|~=|>=|<=|>|<|!=)\s*([^;\s]+))?", line)
        if match:
            deps.append(DeclaredDependency("pypi", match.group(1), match.group(2), path))


def _toml_like_dependencies(path: str, content: str, ecosystem: str, deps: list[DeclaredDependency]) -> None:
    section: str | None = None
    lines = content.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        header = re.match(r"\[([^]]+)\]", line)
        if header:
            section = header.group(1).casefold()
            index += 1
            continue
        if ecosystem == "pypi" and section == "project" and re.match(r"dependencies\s*=\s*\[", line):
            array_lines = [line]
            while "]" not in array_lines[-1] and index + 1 < len(lines):
                index += 1
                array_lines.append(lines[index])
            for requirement in re.findall(r'"([^"]+)"', "\n".join(array_lines)):
                match = re.match(r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*(?:(?:==|~=|>=|<=|>|<|!=)\s*([^;\s]+))?", requirement)
                if match:
                    deps.append(DeclaredDependency(ecosystem, match.group(1), match.group(2), path))
            index += 1
            continue
        if ecosystem == "pypi" and section not in {"tool.poetry.dependencies", "dependency-groups.dev"}:
            index += 1
            continue
        if ecosystem == "cargo" and not (
            section == "dependencies"
            or ((section or "").startswith("target.") and (section or "").endswith(".dependencies"))
        ):
            index += 1
            continue
        match = re.match(
            r'([A-Za-z0-9_.-]+)\s*=\s*(?:"([^"]+)"|\{[^}]*version\s*=\s*"([^"]+)"[^}]*\})',
            line,
        )
        if match and not (ecosystem == "pypi" and match.group(1).casefold() == "python"):
            deps.append(DeclaredDependency(ecosystem, match.group(1), match.group(2) or match.group(3), path))
        index += 1

def _go_dependencies(path: str, content: str, deps: list[DeclaredDependency]) -> None:
    for raw in content.splitlines():
        match = re.match(r"\s*([^\s()]+)\s+(v[0-9][^\s]+)", raw)
        if match and not match.group(1).startswith("module"):
            deps.append(DeclaredDependency("go", match.group(1), match.group(2), path))


def _maven_dependencies(path: str, content: str, deps: list[DeclaredDependency], warnings: list[str]) -> None:
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        warnings.append(f"{path}: invalid XML manifest.")
        return
    for item in root.iter():
        if item.tag.split("}")[-1] != "dependency":
            continue
        values = {
            child.tag.split("}")[-1]: (child.text or "").strip()
            for child in item
        }
        if values.get("groupId") and values.get("artifactId"):
            deps.append(DeclaredDependency(
                "maven",
                values["groupId"] + ":" + values["artifactId"],
                values.get("version") or None,
                path,
            ))


def analyze_project(files: Mapping[str, str], entry: str | None = None) -> StackAnalysis:
    """Identify known host stacks and declared dependencies from supplied files."""
    normalized = _normal_files(files)
    found: dict[str, HostStack] = {}
    dependencies: list[DeclaredDependency] = []
    warnings: list[str] = []
    module_graph: dict[str, object] | None = None

    for path, content in sorted(normalized.items()):
        name = posixpath.basename(path).casefold()
        if name == "package.json":
            _package_json(path, content, found, dependencies, warnings)
        elif name == "requirements.txt":
            _add_stack(found, HostStack("python", "python", path, ("requirements.txt",), 0.85))
            _requirements(path, content, dependencies)
        elif name == "pyproject.toml":
            _add_stack(found, HostStack("python", "python", path, ("pyproject.toml",), 0.92))
            _toml_like_dependencies(path, content, "pypi", dependencies)
        elif name == "cargo.toml":
            _add_stack(found, HostStack("rust", "rust", path, ("Cargo.toml",), 0.95))
            _toml_like_dependencies(path, content, "cargo", dependencies)
        elif name == "go.mod":
            _add_stack(found, HostStack("go", "go", path, ("go.mod",), 0.95))
            _go_dependencies(path, content, dependencies)
        elif name == "pom.xml":
            _add_stack(found, HostStack("java", "java", path, ("Maven pom.xml",), 0.95))
            _maven_dependencies(path, content, dependencies, warnings)
        elif name in {"build.gradle", "build.gradle.kts"}:
            _add_stack(found, HostStack("gradle", "kotlin/java", path, ("Gradle build file",), 0.85))
            if "com.android.application" in content or "com.android.library" in content:
                _add_stack(found, HostStack("android", "kotlin/java", path, ("Android Gradle plugin",), 0.98))
            for match in re.finditer(r'(?:implementation|api|compileOnly|runtimeOnly)\s*\(?\s*["\']([^:"\']+):([^:"\']+):([^"\']+)["\']', content):
                dependencies.append(DeclaredDependency("gradle", match.group(1) + ":" + match.group(2), match.group(3), path))
        elif name == "androidmanifest.xml":
            _add_stack(found, HostStack("android", "kotlin/java", path, ("AndroidManifest.xml",), 0.98))
        elif name == "package.swift":
            _add_stack(found, HostStack("swift", "swift", path, ("Package.swift",), 0.95))
            for match in re.finditer(r'\.package\([^)]*url\s*:\s*"([^"]+)"[^)]*from\s*:\s*"([^"]+)"', content):
                package_name = match.group(1).rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
                dependencies.append(DeclaredDependency("swiftpm", package_name, match.group(2), path))
        elif name.endswith(".csproj"):
            _add_stack(found, HostStack("dotnet", "csharp", path, ("C# project file",), 0.95))
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(content)
                for item in root.iter():
                    if item.tag.split("}")[-1] == "PackageReference":
                        package_name = item.attrib.get("Include") or item.attrib.get("Update")
                        version = item.attrib.get("Version")
                        if package_name:
                            dependencies.append(DeclaredDependency("nuget", package_name, version, path))
            except ET.ParseError:
                warnings.append(f"{path}: invalid XML project file.")
        elif name == "cmakelists.txt":
            _add_stack(found, HostStack("cmake", "c/c++", path, ("CMakeLists.txt",), 0.8))
            for match in re.finditer(r"find_package\s*\(\s*([A-Za-z0-9_.+-]+)(?:\s+([0-9][^\s)]+))?", content, re.IGNORECASE):
                dependencies.append(DeclaredDependency("cmake", match.group(1), match.group(2), path))
        elif name.endswith(".cudl"):
            from .bundle import parse_bundle
            parsed = parse_bundle(content, source=path)
            if not parsed.has_errors:
                guide = parsed.bundle.sections.get("guide", [])
                for node in guide:
                    if node.kind.casefold() not in {"target", "targets"}:
                        continue
                    raw = node.value.strip()
                    if raw.startswith("="):
                        raw = raw[1:].strip()
                    raw = raw.strip("[]")
                    profiles = {
                        "react": ("react", "javascript"),
                        "react-native": ("react-native", "javascript"),
                        "web": ("web", "javascript"),
                        "python": ("python", "python"),
                        "android": ("android", "kotlin/java"),
                        "ios": ("ios", "swift"),
                    }
                    for part in raw.split(","):
                        target = part.strip().strip(chr(34) + chr(39)).casefold()
                        if target in profiles:
                            stack_name, language = profiles[target]
                            _add_stack(found, HostStack(
                                stack_name, language, path,
                                ("explicit CUDL GUIDE target",), 1.0,
                            ))

    ordered = sorted(found.values(), key=lambda item: (-item.confidence, item.name))
    unique_dependencies: dict[tuple[str, str, str | None], DeclaredDependency] = {}
    for item in dependencies:
        unique_dependencies.setdefault((item.ecosystem, item.name.casefold(), item.version), item)

    versions: dict[tuple[str, str], set[str]] = {}
    for item in unique_dependencies.values():
        if item.version:
            versions.setdefault((item.ecosystem, item.name.casefold()), set()).add(item.version)
    for (ecosystem, dependency_name), declared_versions in sorted(versions.items()):
        if len(declared_versions) > 1:
            warnings.append(
                f"Conflicting declared versions for {ecosystem} dependency {dependency_name}: "
                + ", ".join(sorted(declared_versions))
            )

    if entry is not None:
        graph = resolve_project(normalized, entry)
        module_graph = graph.to_dict()
        warnings.extend(
            f"{item.code}: {item.message}"
            for item in graph.diagnostics
        )

    return StackAnalysis(
        stacks=ordered,
        dependencies=list(unique_dependencies.values()),
        warnings=warnings,
        module_graph=module_graph,
    )
