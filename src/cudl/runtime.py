"""Safe reference runtime for CUDL's beginner-first native script subset.

The runtime deliberately interprets a small, explicit grammar. It never uses
eval/exec, imports host modules, or runs external-language blocks.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import math
import operator
import re
from typing import Any

from .expressions import ExpressionError, parse_expression, resolve_path
from .parser import Document, Node, parse


class CUDLRuntimeError(ValueError):
    """A source-level error raised while running supported native CUDL code."""

    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    variables: dict[str, object]
    output: list[str]
    steps: int

    def to_dict(self) -> dict[str, object]:
        return {
            "variables": self.variables,
            "output": list(self.output),
            "steps": self.steps,
        }


@dataclass(frozen=True, slots=True)
class _Function:
    name: str
    parameters: tuple[str, ...]
    body: tuple[Node, ...]
    line: int


class _ReturnSignal(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


class _Scope:
    def __init__(self, initial: dict[str, object] | None = None, parent: "_Scope | None" = None) -> None:
        self.values = {key.casefold(): value for key, value in (initial or {}).items()}
        self.constants: set[str] = set()
        self.parent = parent

    def get(self, name: str) -> object:
        key = name.casefold()
        if key in self.values:
            return self.values[key]
        if self.parent is not None:
            return self.parent.get(key)
        raise CUDLRuntimeError(f"Unknown variable #{name}.")

    def set(self, name: str, value: object, *, constant: bool = False, line: int | None = None) -> None:
        key = name.casefold()
        if key in self.constants:
            raise CUDLRuntimeError(f"Constant #{name} cannot be reassigned.", line)
        self.values[key] = value
        if constant:
            self.constants.add(key)

    def mapping(self) -> dict[str, object]:
        result = self.parent.mapping() if self.parent is not None else {}
        result.update(self.values)
        return result


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ASSIGNMENT = re.compile(r"^#([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", re.DOTALL)
_CONST_ASSIGNMENT = re.compile(r"^#([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", re.DOTALL)
_FUNCTION_CALL = re.compile(r"^@([A-Za-z_][A-Za-z0-9_-]*)(?:\s+(.*))?$", re.DOTALL)
_VARIABLE_PATH = re.compile(
    r"#(?:[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*|\[(?:0|[1-9]\d*|[A-Za-z_][A-Za-z0-9_]*|'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\")\])*)"
)


def _read_hash_path(source: str, start: int) -> int:
    """Return the end of a hash path, leaving validation to parse_expression."""
    index = start + 1
    root = _IDENTIFIER.match(source, index)
    if not root:
        raise CUDLRuntimeError("A variable reference must use #name.")
    index = root.end()
    while index < len(source):
        if source[index] == ".":
            part = _IDENTIFIER.match(source, index + 1)
            if not part:
                raise CUDLRuntimeError("Expected a property name after '.'.")
            index = part.end()
        elif source[index] == "[":
            quote: str | None = None
            escaped = False
            end = index + 1
            while end < len(source):
                char = source[end]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == quote:
                        quote = None
                elif char in ("'", '"'):
                    quote = char
                elif char == "]":
                    break
                end += 1
            if end >= len(source):
                raise CUDLRuntimeError("Index is missing its closing ']'.")
            index = end + 1
        else:
            break
    return index


def _replace_paths(source: str, scope: _Scope) -> tuple[str, dict[str, object]]:
    """Replace hash paths outside strings with inert names for safe AST parsing."""
    output: list[str] = []
    values: dict[str, object] = {}
    quote: str | None = None
    escaped = False
    index = 0

    while index < len(source):
        char = source[index]
        if quote is not None:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "#":
            end = _read_hash_path(source, index)
            raw_path = source[index:end]
            try:
                expression = parse_expression(raw_path)
                value = resolve_path(expression, scope.mapping())
            except (ExpressionError, KeyError) as exc:
                raise CUDLRuntimeError(str(exc)) from exc
            placeholder = f"__cudl_path_{len(values)}"
            values[placeholder] = value
            output.append(placeholder)
            index = end
            continue
        output.append(char)
        index += 1
    return "".join(output), values


def _normalize_literals(source: str) -> str:
    """Translate CUDL's lowercase typed literals without changing quoted text."""
    output: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    literals = {"true": "True", "false": "False", "null": "None"}
    while index < len(source):
        char = source[index]
        if quote is not None:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            output.append(char)
            index += 1
            continue
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            word = source[index:end]
            output.append(literals.get(word.casefold(), word))
            index = end
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _finite(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        raise CUDLRuntimeError("Numeric results must be finite.")
    return value


def _safe_expression(source: str, scope: _Scope) -> object:
    replaced, paths = _replace_paths(source, scope)
    replaced = _normalize_literals(replaced)
    try:
        tree = ast.parse(replaced, mode="eval")
    except SyntaxError as exc:
        raise CUDLRuntimeError("Invalid CUDL expression.") from exc

    def visit(node: ast.AST, *, allow_bare_word: bool = False) -> object:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.List):
            if len(node.elts) > 1000:
                raise CUDLRuntimeError("A list literal cannot contain more than 1000 items.")
            return [visit(item, allow_bare_word=True) for item in node.elts]
        if isinstance(node, ast.Tuple):
            if len(node.elts) > 1000:
                raise CUDLRuntimeError("A tuple literal cannot contain more than 1000 items.")
            return tuple(visit(item, allow_bare_word=True) for item in node.elts)
        if isinstance(node, ast.Dict):
            if len(node.keys) > 100:
                raise CUDLRuntimeError("A mapping literal cannot contain more than 100 entries.")
            result: dict[object, object] = {}
            for key_node, value_node in zip(node.keys, node.values):
                if key_node is None:
                    raise CUDLRuntimeError("Mapping unpacking is not supported.")
                key = visit(key_node, allow_bare_word=True)
                if not isinstance(key, (str, int, float, bool)):
                    raise CUDLRuntimeError("Mapping keys must be simple values.")
                if key in result:
                    raise CUDLRuntimeError("Mapping keys must be unique.")
                result[key] = visit(value_node, allow_bare_word=True)
            return result
        if isinstance(node, ast.Constant):
            value = node.value
            if value is None or isinstance(value, (str, bool, int, float)):
                return _finite(value)
            raise CUDLRuntimeError("Only simple values are allowed in expressions.")
        if isinstance(node, ast.Name):
            if node.id in paths:
                return paths[node.id]
            if allow_bare_word:
                return node.id
            raise CUDLRuntimeError("Only #variable references are allowed in expressions.")
        if isinstance(node, ast.UnaryOp):
            value = visit(node.operand)
            if isinstance(node.op, ast.Not):
                return not bool(value)
            if not _is_number(value):
                raise CUDLRuntimeError("Unary numeric operators require a number.")
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return _finite(-value)
            raise CUDLRuntimeError("Unsupported unary operator.")
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add) and isinstance(left, str) and isinstance(right, str):
                return left + right
            if not _is_number(left) or not _is_number(right):
                raise CUDLRuntimeError("Arithmetic operators require numbers (or two strings with +).")
            operations = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }
            operation = operations.get(type(node.op))
            if operation is None:
                raise CUDLRuntimeError("Unsupported arithmetic operator.")
            if isinstance(node.op, ast.Pow) and abs(float(right)) > 1000:
                raise CUDLRuntimeError("Exponent is too large.")
            try:
                return _finite(operation(left, right))
            except (ArithmeticError, OverflowError, ValueError) as exc:
                raise CUDLRuntimeError("Arithmetic operation failed.") from exc
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result: object = True
                for child in node.values:
                    result = visit(child)
                    if not bool(result):
                        return result
                return result
            if isinstance(node.op, ast.Or):
                result = False
                for child in node.values:
                    result = visit(child)
                    if bool(result):
                        return result
                return result
            raise CUDLRuntimeError("Unsupported logical operator.")
        if isinstance(node, ast.Compare):
            left = visit(node.left)
            comparisons = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
            }
            for operator_node, comparator in zip(node.ops, node.comparators):
                right = visit(comparator)
                operation = comparisons.get(type(operator_node))
                if operation is None:
                    raise CUDLRuntimeError("Unsupported comparison operator.")
                if type(operator_node) not in (ast.Eq, ast.NotEq) and not (
                    (_is_number(left) and _is_number(right)) or
                    (type(left) is type(right) and isinstance(left, (str, bool)))
                ):
                    raise CUDLRuntimeError("Values cannot be ordered because their types differ.")
                try:
                    matched = operation(left, right)
                except TypeError as exc:
                    raise CUDLRuntimeError("Values cannot be compared.") from exc
                if not matched:
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return visit(node.body if bool(visit(node.test)) else node.orelse)
        raise CUDLRuntimeError(f"Unsupported expression element: {type(node).__name__}.")

    return visit(tree)


def _split_arguments(source: str) -> list[str]:
    values: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    bracket_depth = 0
    for index, char in enumerate(source):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char.isspace() and bracket_depth == 0:
            token = source[start:index].strip()
            if token:
                values.append(token)
            start = index + 1
    token = source[start:].strip()
    if token:
        values.append(token)
    return values


class _Interpreter:
    def __init__(self, document: Document, data: dict[str, object] | None = None) -> None:
        self.document = document
        self.global_scope = _Scope(data)
        self.functions: dict[str, _Function] = {}
        self.output: list[str] = []
        self.steps = 0
        self.max_steps = 10_000
        self.max_call_depth = 64
        self.script_nodes = [node for node in document.nodes if node.kind.casefold() == "script"]
        self._register_functions()

    def _tick(self, node: Node) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise CUDLRuntimeError("Execution step limit exceeded.", node.line)

    def _register_functions(self) -> None:
        for script in self.script_nodes:
            for node in script.children:
                if not node.kind.startswith("@") or not node.children:
                    continue
                name = node.kind[1:].casefold()
                raw_parameters = node.value.split()
                if any(not re.fullmatch(r"#[A-Za-z_][A-Za-z0-9_]*", item) for item in raw_parameters):
                    raise CUDLRuntimeError(
                        f"Function @{name} parameters must be hash-prefixed names.",
                        node.line,
                    )
                parameters = tuple(item[1:].casefold() for item in raw_parameters)
                if len(set(parameters)) != len(parameters):
                    raise CUDLRuntimeError(f"Function @{name} has duplicate parameters.", node.line)
                if name in self.functions:
                    raise CUDLRuntimeError(f"Function @{name} is declared more than once.", node.line)
                self.functions[name] = _Function(name, parameters, tuple(node.children), node.line)

    def _evaluate(self, source: str, scope: _Scope, line: int, depth: int) -> object:
        raw = source.strip()
        if not raw:
            return None
        if raw.startswith("@"):
            return self._call(raw, scope, line, depth)

        if raw.startswith(('"', "'")):
            try:
                return parse_expression(raw).value
            except ExpressionError as exc:
                raise CUDLRuntimeError(str(exc), line) from exc
        if raw.startswith("[") or raw.startswith("{"):
            try:
                return _safe_expression(raw, scope)
            except CUDLRuntimeError as exc:
                if exc.line is None:
                    exc.line = line
                raise

        has_hash = "#" in raw
        has_operator = bool(re.search(r"(?:==|!=|<=|>=|[+*/%<>])|(?<!^)-(?!>)|\b(?:and|or|not)\b", raw))
        numeric_expression = bool(re.match(r"^(?:\d|true\b|false\b|null\b)", raw, re.IGNORECASE)) and has_operator
        if has_operator and (has_hash or numeric_expression):
            try:
                return _safe_expression(raw, scope)
            except CUDLRuntimeError as exc:
                if exc.line is None:
                    exc.line = line
                raise

        if raw.startswith("#") and not re.search(r"\s", raw):
            try:
                expression = parse_expression(raw)
                return resolve_path(expression, scope.mapping())
            except (ExpressionError, KeyError) as exc:
                raise CUDLRuntimeError(str(exc), line) from exc

        if has_hash:
            def replace(match: re.Match[str]) -> str:
                try:
                    expression = parse_expression(match.group(0))
                    return str(resolve_path(expression, scope.mapping()))
                except (ExpressionError, KeyError) as exc:
                    raise CUDLRuntimeError(str(exc), line) from exc
            return _VARIABLE_PATH.sub(replace, raw)

        try:
            return parse_expression(raw).value
        except ExpressionError as exc:
            raise CUDLRuntimeError(str(exc), line) from exc

    def _call(self, source: str, caller: _Scope, line: int, depth: int) -> object:
        match = _FUNCTION_CALL.fullmatch(source.strip())
        if not match:
            raise CUDLRuntimeError("Function calls use: @name arguments", line)
        name = match.group(1).casefold()
        function = self.functions.get(name)
        if function is None:
            raise CUDLRuntimeError(f"Unknown function @{name}.", line)
        if depth >= self.max_call_depth:
            raise CUDLRuntimeError("Function call depth limit exceeded.", line)

        raw_arguments = match.group(2) or ""
        if len(function.parameters) == 0:
            arguments = [] if not raw_arguments.strip() else _split_arguments(raw_arguments)
        elif len(function.parameters) == 1:
            arguments = [raw_arguments] if raw_arguments.strip() else []
        else:
            arguments = _split_arguments(raw_arguments)
        if len(arguments) != len(function.parameters):
            raise CUDLRuntimeError(
                f"Function @{name} expects {len(function.parameters)} argument(s), received {len(arguments)}.",
                line,
            )

        values = {
            parameter: self._evaluate(argument, caller, line, depth)
            for parameter, argument in zip(function.parameters, arguments)
        }
        local = _Scope(values, self.global_scope)
        try:
            self._execute_nodes(function.body, local, depth + 1)
        except _ReturnSignal as signal:
            return signal.value
        return None

    def _execute_node(self, node: Node, scope: _Scope, depth: int, *, in_function: bool) -> None:
        self._tick(node)
        kind = node.kind.casefold()
        if kind.startswith("@"):
            if node.children:
                return
            self._call("@" + node.kind[1:] + (" " + node.value if node.value else ""), scope, node.line, depth)
            return
        if kind == "variable":
            match = _ASSIGNMENT.fullmatch(node.value)
            if not match:
                raise CUDLRuntimeError("Use #name = value for assignment.", node.line)
            name, expression = match.groups()
            value = self._evaluate(expression, scope, node.line, depth)
            scope.set(name, value, line=node.line)
            return
        if kind == "const":
            match = _CONST_ASSIGNMENT.fullmatch(node.value)
            if not match:
                raise CUDLRuntimeError("Use const #name = value for a constant.", node.line)
            name, expression = match.groups()
            value = self._evaluate(expression, scope, node.line, depth)
            scope.set(name, value, constant=True, line=node.line)
            return
        if kind == "print":
            value = self._evaluate(node.value, scope, node.line, depth)
            self.output.append("" if value is None else str(value))
            return
        if kind == "return":
            if not in_function:
                raise CUDLRuntimeError("return can only be used inside a function.", node.line)
            raise _ReturnSignal(self._evaluate(node.value, scope, node.line, depth))
        if kind in {"js", "javascript", "python", "java", "c", "cpp", "rust", "go", "swift", "kotlin"}:
            return
        raise CUDLRuntimeError(f"Statement '{node.kind}' is not supported by the current CUDL runtime.", node.line)

    def _execute_nodes(self, nodes: list[Node] | tuple[Node, ...], scope: _Scope, depth: int, *, in_function: bool = True) -> None:
        for node in nodes:
            self._execute_node(node, scope, depth, in_function=in_function)

    def run(self) -> RuntimeResult:
        for node in self.document.nodes:
            if node.kind.casefold() == "script":
                self._execute_nodes(node.children, self.global_scope, 0, in_function=False)
            elif node.kind == "variable" or node.kind.casefold() in {"const", "print"}:
                self._execute_node(node, self.global_scope, 0, in_function=False)
        return RuntimeResult(
            variables=self.global_scope.mapping(),
            output=self.output,
            steps=self.steps,
        )


def run_script(source: str, data: dict[str, object] | None = None) -> RuntimeResult:
    """Parse and run supported native CUDL statements without executing host code."""
    parsed = parse(source)
    if parsed.has_errors:
        details = "; ".join(
            f"{item.code} at line {item.line}: {item.message}"
            for item in parsed.diagnostics
        )
        raise CUDLRuntimeError(details)
    return _Interpreter(parsed.document, data).run()
