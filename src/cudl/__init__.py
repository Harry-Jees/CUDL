"""CUDL language core."""

from .diagnostics import Diagnostic, Severity
from .lexer import LexError, Token, TokenKind, tokenize
from .parser import Document, Node, ParseResult, parse

__all__ = [
    "Diagnostic",
    "Document",
    "LexError",
    "Node",
    "ParseResult",
    "Severity",
    "Token",
    "TokenKind",
    "parse",
    "tokenize",
]

__version__ = "0.1.0"
