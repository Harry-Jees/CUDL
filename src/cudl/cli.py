"""Command-line entry point for the CUDL prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .parser import parse
from .lexer import LexError, tokenize


def _parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="cudl", description="CUDL language tools")
    commands = cli.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("check", "Parse a CUDL file and report diagnostics."),
        ("parse", "Parse a CUDL file and print its syntax tree as JSON."),
        ("tokens", "Tokenize a CUDL file and print tokens as JSON."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path)
    return cli


def main() -> int:
    args = _parser().parse_args()
    try:
        source = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    if args.command == "tokens":
        try:
            print(json.dumps([token.to_dict() for token in tokenize(source)], indent=2))
            return 0
        except LexError as exc:
            print(f"{args.file}:{exc.line}:{exc.column}: error CUDL0001: {exc.message}", file=sys.stderr)
            return 1

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
