"""CUDL language core."""

from .diagnostics import Diagnostic, Severity
from .parser import Document, Node, ParseResult, parse

__all__ = [
    "Diagnostic",
    "Document",
    "Node",
    "ParseResult",
    "Severity",
    "parse",
]

__version__ = "0.1.0"
