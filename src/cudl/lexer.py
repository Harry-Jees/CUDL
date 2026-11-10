"""Tokenizer for the first CUDL language grammar.

The lexer preserves line and column positions and emits indentation tokens.
It does not assign meaning to UI words; that is handled by later parser and
semantic passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenKind(str, Enum):
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    NEWLINE = "NEWLINE"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    ARROW = "ARROW"
    COLON = "COLON"
    COMMA = "COMMA"
    DOT = "DOT"
    AT = "AT"
    HASH = "HASH"
    OPERATOR = "OPERATOR"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    value: str
    line: int
    column: int

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "value": self.value,
            "line": self.line,
            "column": self.column,
        }


class LexError(ValueError):
    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


_SINGLE = {
    ":": TokenKind.COLON,
    ",": TokenKind.COMMA,
    ".": TokenKind.DOT,
    "@": TokenKind.AT,
    "#": TokenKind.HASH,
    "[": TokenKind.LBRACKET,
    "]": TokenKind.RBRACKET,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
}
_OPERATORS = set("=+-*/%<>!")
_ESCAPES = {"n": "\\n", "r": "\\r", "t": "\\t", '"': '"', "\\\\": "\\\\"}


def tokenize(source: str) -> list[Token]:
    """Convert CUDL source into tokens, including indentation structure.

    Double hash starts a comment. A single hash is a variable marker and is
    emitted as a HASH token.
    """
    tokens: list[Token] = []
    indents = [0]
    lines = source.splitlines()

    for line_no, raw in enumerate(lines, start=1):
        if not raw.strip() or raw.lstrip().startswith("##"):
            continue

        prefix = raw[: len(raw) - len(raw.lstrip(" "))]
        if "\\t" in raw[: len(raw) - len(raw.lstrip(" \\t"))]:
            raise LexError("Tabs are not allowed for indentation; use spaces.", line_no, 1)

        width = len(prefix)
        if width % 4:
            raise LexError("Indentation must use multiples of four spaces.", line_no, 1)

        if width > indents[-1]:
            if width != indents[-1] + 4:
                raise LexError("Unexpected indentation level.", line_no, width + 1)
            indents.append(width)
            tokens.append(Token(TokenKind.INDENT, "", line_no, 1))
        elif width < indents[-1]:
            while width < indents[-1]:
                indents.pop()
                tokens.append(Token(TokenKind.DEDENT, "", line_no, width + 1))
            if width != indents[-1]:
                raise LexError("Indentation does not match an earlier block.", line_no, width + 1)

        i = width
        while i < len(raw):
            char = raw[i]
            if char.isspace():
                i += 1
                continue
            if raw.startswith("##", i):
                break
            column = i + 1

            if char in ('"', "'"):
                quote = char
                start = i
                i += 1
                value: list[str] = []
                while i < len(raw) and raw[i] != quote:
                    if raw[i] == "\\\\":
                        i += 1
                        if i >= len(raw):
                            raise LexError("Unterminated escape sequence.", line_no, i + 1)
                        value.append(_ESCAPES.get(raw[i], raw[i]))
                    else:
                        value.append(raw[i])
                    i += 1
                if i >= len(raw):
                    raise LexError("Unterminated string literal.", line_no, start + 1)
                i += 1
                tokens.append(Token(TokenKind.STRING, "".join(value), line_no, column))
                continue

            if raw.startswith("->", i):
                tokens.append(Token(TokenKind.ARROW, "->", line_no, column))
                i += 2
                continue

            if char in _SINGLE:
                tokens.append(Token(_SINGLE[char], char, line_no, column))
                i += 1
                continue

            if char in _OPERATORS:
                start = i
                i += 1
                while i < len(raw) and raw[i] in _OPERATORS:
                    i += 1
                tokens.append(Token(TokenKind.OPERATOR, raw[start:i], line_no, column))
                continue

            if char.isdigit():
                start = i
                i += 1
                while i < len(raw) and (raw[i].isalnum() or raw[i] in "._"):
                    i += 1
                tokens.append(Token(TokenKind.NUMBER, raw[start:i], line_no, column))
                continue

            if char.isalpha() or char == "_":
                start = i
                i += 1
                while i < len(raw) and (raw[i].isalnum() or raw[i] in "_-"):
                    i += 1
                tokens.append(Token(TokenKind.IDENTIFIER, raw[start:i], line_no, column))
                continue

            raise LexError(f"Unexpected character {char!r}.", line_no, column)

        tokens.append(Token(TokenKind.NEWLINE, "\\n", line_no, len(raw) + 1))

    final_line = max(1, len(lines))
    while len(indents) > 1:
        indents.pop()
        tokens.append(Token(TokenKind.DEDENT, "", final_line, 1))
    tokens.append(Token(TokenKind.EOF, "", final_line, 1))
    return tokens
