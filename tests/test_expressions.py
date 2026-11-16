import pytest

from cudl.expressions import ExpressionError, parse_expression, resolve_path


@pytest.mark.parametrize(
    ("source", "kind", "value"),
    [
        ('"Hello"', "string", "Hello"),
        ("'Hello\\nworld'", "string", "Hello\nworld"),
        ("Hello from CUDL", "string", "Hello from CUDL"),
        ("profile.png", "string", "profile.png"),
        ("get_name()", "string", "get_name()"),
        ("a + b", "string", "a + b"),
        ("42", "number", 42),
        ("-2.5", "number", -2.5),
        ("true", "boolean", True),
        ("FALSE", "boolean", False),
        ("null", "null", None),
    ],
)
def test_parses_dynamic_values_without_executing_text(source, kind, value):
    expression = parse_expression(source)
    assert expression.kind == kind
    assert expression.value == value


def test_parses_hash_prefixed_data_path():
    expression = parse_expression("#user.profile.display_name")
    assert expression.kind == "path"
    assert expression.path == ("user", "profile", "display_name")
    assert resolve_path(expression, {"user": {"profile": {"display_name": "Harry"}}}) == "Harry"


def test_parses_list_and_mapping_indexes():
    users = [{"name": "Ada"}, {"name": "Harry"}]
    assert resolve_path(parse_expression("#users[1].name"), {"users": users}) == "Harry"
    assert resolve_path(parse_expression("#user[name]"), {"user": {"name": "Ada"}}) == "Ada"
    assert resolve_path(
        parse_expression('#user["display-name"]'),
        {"user": {"display-name": "Harry"}},
    ) == "Harry"


@pytest.mark.parametrize(
    "source",
    ["", "#", "#items[-1]", "#items[]", "#user.", "#user[name", "#user[1.5]"],
)
def test_rejects_malformed_hash_paths(source):
    with pytest.raises(ExpressionError):
        parse_expression(source)


def test_missing_path_or_index_is_reported():
    with pytest.raises(KeyError):
        resolve_path(parse_expression("#user.name"), {"user": {}})
    with pytest.raises(KeyError):
        resolve_path(parse_expression("#items[3]"), {"items": [1]})


def test_expression_serialization_is_stable():
    assert parse_expression("#user.name").to_dict() == {
        "kind": "path", "value": "#user.name", "path": ["user", "name"]
    }
