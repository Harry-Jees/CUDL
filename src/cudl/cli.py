"""Command-line entry point for the CUDL prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .parser import parse
from .modules import resolve_project
from .lexer import LexError, tokenize
from .runtime import CUDLRuntimeError, run_script
from .bundle import lower_bundle, parse_bundle
from .time import compile_time
from .routing import DeviceContext, compile_component_routes, resolve_component_route
from .picker import filter_scripts_for_hosts


def _parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="cudl", description="CUDL language tools")
    commands = cli.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("check", "Parse a CUDL file and report diagnostics."),
        ("parse", "Parse a CUDL file and print its syntax tree as JSON."),
        ("tokens", "Tokenize a CUDL file and print tokens as JSON."),
        ("bundle", "Validate a five-part bundle and print its application IR."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path)
    run = commands.add_parser("run", help="Run supported native CUDL script blocks.")
    run.add_argument("file", type=Path)
    routes = commands.add_parser("routes", help="Preview the selected KIT implementation for a device.")
    routes.add_argument("file", type=Path)
    routes.add_argument("--component", required=True)
    routes.add_argument("--platform", required=True)
    routes.add_argument("--device", default="any")
    routes.add_argument("--width", type=int)
    routes.add_argument("--input", dest="input_mode")
    routes.add_argument("--capability", action="append", default=[])
    picker = commands.add_parser("picker", help="Preview native script blocks selected for a host.")
    picker.add_argument("file", type=Path)
    picker.add_argument("--host", action="append", required=True, help="Declared host profile; repeat for independent multi-host previews.")
    picker.add_argument("--extra-language", action="append", default=[], help="Additional native language supported by the host; may be repeated.")
    graph = commands.add_parser("graph", help="Resolve project imports and print the module graph.")
    graph.add_argument("project", type=Path)
    graph.add_argument("entry", help="Entry module path relative to the project root.")
    return cli


def main() -> int:
    args = _parser().parse_args()
    if args.command == "graph":
        if not args.project.is_dir():
            print(f"error: project directory does not exist: {args.project}", file=sys.stderr)
            return 2
        sources = {
            path.relative_to(args.project).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(args.project.rglob("*.cudl"))
            if path.is_file()
        }
        graph = resolve_project(sources, args.entry)
        print(json.dumps(graph.to_dict(), indent=2))
        return 1 if graph.has_errors else 0

    try:
        source = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    if args.command == "picker":
        result = parse_bundle(source, source=str(args.file))
        for diagnostic in result.diagnostics:
            location = f"{diagnostic.source or '<input>'}:{diagnostic.line}:{diagnostic.column}"
            print(f"{location}: {diagnostic.severity.value} {diagnostic.code}: {diagnostic.message}", file=sys.stderr)
            if diagnostic.suggestion:
                print(f"  suggestion: {diagnostic.suggestion}", file=sys.stderr)
        if result.has_errors:
            return 1
        try:
            extra_languages = {host.strip().casefold(): args.extra_language for host in args.host}
            selections = filter_scripts_for_hosts(
                result.bundle.sections.get("scripts", []), args.host, extra_languages
            )
        except ValueError as exc:
            print(f"{args.file}: error CUDL7001: {exc}", file=sys.stderr)
            return 2
        for selection in selections.values():
            for language, line in selection.unsupported:
                print(
                    f"{args.file}:{line}: warning CUDL7002: unsupported script language {language!r} was excluded.",
                    file=sys.stderr,
                )
        if len(selections) == 1:
            payload = next(iter(selections.values())).to_dict()
        else:
            payload = {
                "type": "CUDLMultiHostPickerSelection",
                "version": 1,
                "selections": [selection.to_dict() for selection in selections.values()],
            }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "routes":
        result = parse_bundle(source, source=str(args.file))
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.code} line {diagnostic.line}: {diagnostic.message}", file=sys.stderr)
        if result.has_errors:
            return 1
        kit_nodes = result.bundle.sections.get("kit", [])
        compiled = compile_component_routes(kit_nodes)
        if compiled.diagnostics:
            for diagnostic in compiled.diagnostics:
                print(diagnostic, file=sys.stderr)
            return 1
        context = DeviceContext(
            platform=args.platform,
            device=args.device,
            width=args.width,
            input=args.input_mode,
            capabilities=frozenset(args.capability),
        )
        resolution = resolve_component_route(args.component, compiled.routes, context)
        print(json.dumps({
            "component": resolution.component,
            "platform": context.platform,
            "device": context.device,
            "implementation": resolution.implementation,
            "reason": resolution.reason,
        }, indent=2))
        return 0 if resolution.implementation else 1

    if args.command == "bundle":
        result = parse_bundle(source, source=str(args.file))
        for diagnostic in result.diagnostics:
            location = f"{diagnostic.source or '<input>'}:{diagnostic.line}:{diagnostic.column}"
            print(f"{location}: {diagnostic.severity.value} {diagnostic.code}: {diagnostic.message}", file=sys.stderr)
            if diagnostic.suggestion:
                print(f"  suggestion: {diagnostic.suggestion}", file=sys.stderr)
        if result.has_errors:
            return 1
        time_result = compile_time(result.bundle)
        for diagnostic in time_result.diagnostics:
            location = str(diagnostic.source or "<input>") + f":{diagnostic.line}:{diagnostic.column}"
            print(f"{location}: {diagnostic.severity.value} {diagnostic.code}: {diagnostic.message}", file=sys.stderr)
            if diagnostic.suggestion:
                print(f"  suggestion: {diagnostic.suggestion}", file=sys.stderr)
        if time_result.has_errors:
            return 1
        payload = {
            "application": lower_bundle(result.bundle).to_dict(),
            "time": time_result.to_dict(),
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "tokens":
        try:
            print(json.dumps([token.to_dict() for token in tokenize(source)], indent=2))
            return 0
        except LexError as exc:
            print(f"{args.file}:{exc.line}:{exc.column}: error CUDL0001: {exc.message}", file=sys.stderr)
            return 1

    if args.command == "run":
        try:
            result = run_script(source)
        except CUDLRuntimeError as exc:
            location = f":{exc.line}" if exc.line is not None else ""
            print(f"{args.file}{location}: error: {exc}", file=sys.stderr)
            return 1
        for line in result.output:
            print(line)
        return 0

    result = parse(source, source=str(args.file))

    if args.command == "parse":
        print(json.dumps(result.document.to_dict(), indent=2))
    for diagnostic in result.diagnostics:
        location = f"{diagnostic.source or '<input>'}:{diagnostic.line}:{diagnostic.column}"
        print(f"{location}: {diagnostic.severity.value} {diagnostic.code}: {diagnostic.message}")
        if diagnostic.suggestion:
            print(f"  suggestion: {diagnostic.suggestion}")

    if args.command == "check" and not result.diagnostics:
        print(f"OK: {args.file}")
    return 1 if result.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
