import pytest

from cudl.lexer import LexError, TokenKind, tokenize


def test_tokenizes_page_and_nested_content():
    tokens = tokenize('page Home\n    title Welcome\n')
    kinds = [token.kind for token in tokens]
    assert kinds == [
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.NEWLINE,
        TokenKind.INDENT,
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.NEWLINE,
        TokenKind.DEDENT,
        TokenKind.EOF,
    ]


def test_tokenizes_navigation_arrow_and_component_reference():
    tokens = tokenize('@Profile -> open')
    assert [token.kind for token in tokens[:-2]] == [
        TokenKind.AT,
        TokenKind.IDENTIFIER,
        TokenKind.ARROW,
        TokenKind.IDENTIFIER,
    ]


def test_tokenizes_hash_variable_and_ignores_double_hash_comment():
    tokens = tokenize("## comment\n#name = Harry ## inline comment\n")
    assert [token.kind for token in tokens] == [
        TokenKind.HASH,
        TokenKind.IDENTIFIER,
        TokenKind.OPERATOR,
        TokenKind.IDENTIFIER,
        TokenKind.NEWLINE,
        TokenKind.EOF,
    ]


def test_decodes_string_escapes():
    tokens = tokenize('text "line\\nnext"')
    string = next(token for token in tokens if token.kind is TokenKind.STRING)
    assert string.value == "line\nnext"


def test_rejects_unclosed_string():
    with pytest.raises(LexError, match="Unterminated string"):
        tokenize('title "unfinished')


def test_rejects_indentation_jump():
    with pytest.raises(LexError, match="Unexpected indentation"):
        tokenize("page Home\n        title jump")
