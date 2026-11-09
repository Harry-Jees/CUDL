import pytest

from cudl.expressions import ExpressionError, parse_expression, resolve_path


@pytest.mark.parametrize(
    ("source", "kind", "value"),
    [
        ('"Hello"', "string", "Hello"),
        ("'Hello\\nworld'", "string", "Hello\nworld"),
        ("42", "number", 42),
        ("-2.5", "number", -2.5),
        ("true", "boolean", True),
        ("FALSE", "boolean", False),
        ("null", "null", None),
    ],
)
def test_parses_literal_values(source, kind, value):
    expression = parse_expression(source)
    assert expression.kind == kind
    assert expression.value == value


def test_parses_dotted_data_path():
    expression = parse_expression("user.profile.display_name")
    assert expression.kind == "path"
    assert expression.path == ("user", "profile", "display_name")
    assert resolve_path(expression, {"user": {"profile": {"display_name": "Harry"}}}) == "Harry"


@pytest.mark.parametrize("source", ["", "user()", "user.name + 'x'", "items[0]", "a-b", "1/0"])
def test_rejects_executable_or_unsupported_expressions(source):
    with pytest.raises(ExpressionError):
        parse_expression(source)


def test_missing_path_is_reported():
    with pytest.raises(KeyError):
        resolve_path(parse_expression("user.name"), {"user": {}})


def test_expression_serialization_is_stable():
    assert parse_expression("user.name").to_dict() == {
        "kind": "path", "value": "user.name", "path": ["user", "name"]
    }
