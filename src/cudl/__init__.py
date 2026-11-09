"""CUDL language core."""

from .diagnostics import Diagnostic, Severity
from .lexer import LexError, Token, TokenKind, tokenize
from .ir import IRDocument, IRNode, lower
from .parser import Document, Node, ParseResult, parse

__all__ = [
    "Diagnostic",
    "Document",
    "LexError",
    "IRDocument",
    "IRNode",
    "Node",
    "ParseResult",
    "Severity",
    "Token",
    "TokenKind",
    "lower",
    "parse",
    "tokenize",
]

__version__ = "0.1.0"
