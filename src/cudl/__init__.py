"""CUDL language core."""

from .diagnostics import Diagnostic, Severity
from .bundle import ApplicationBundle, ApplicationIR, BundleParseResult, lower_bundle, parse_bundle
from .time import Keyframe, Scene, TimeCompileError, TimeCompileResult, Timeline, Track, compile_time, parse_time_us
from .expressions import Expression, ExpressionError, parse_expression, resolve_path
from .components import ComponentDefinition, ComponentProperty, ComponentRegistry, build_component_registry
from .lexer import LexError, Token, TokenKind, tokenize
from .ir import IRDocument, IRNode, lower
from .modules import ImportBinding, ImportSpec, ModuleGraph, parse_import, resolve_project
from .parser import Document, Node, ParseResult, parse
from .routing import (
    ComponentRoute, DeviceContext, RouteCompileResult, RouteResolution,
    compile_component_routes, resolve_component_route,
)
from .runtime import CUDLRuntimeError, RuntimeResult, run_script

__all__ = [
    "Diagnostic", "ApplicationBundle", "ApplicationIR", "BundleParseResult",
    "parse_bundle", "lower_bundle", "Keyframe", "Scene", "TimeCompileError",
    "TimeCompileResult", "Timeline", "Track", "compile_time", "parse_time_us",
    "CUDLRuntimeError", "RuntimeResult", "run_script", "Expression",
    "ExpressionError", "parse_expression", "resolve_path", "ComponentDefinition",
    "ComponentProperty", "ComponentRegistry", "build_component_registry",
    "Document", "LexError", "IRDocument", "IRNode", "ImportBinding",
    "ImportSpec", "ModuleGraph", "Node", "ParseResult", "Severity", "Token",
    "TokenKind", "lower", "parse", "parse_import", "resolve_project",
    "tokenize", "ComponentRoute", "DeviceContext", "RouteCompileResult",
    "RouteResolution", "compile_component_routes", "resolve_component_route",
]

__version__ = "0.1.0"
