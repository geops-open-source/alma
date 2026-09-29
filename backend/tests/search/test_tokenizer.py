import pytest

from alma.search.tokenizer import Token, Tokenizer
from alma.search.tokenizer import TokenType as T


def get_tokens(s: str, skip_ws: bool = True) -> list[Token]:
    tokenizer = Tokenizer(s)
    result: list[Token] = []

    while token := tokenizer.get_next_token():
        if not (skip_ws and token.type == T.WS):
            result.append(token)

    return result


@pytest.mark.parametrize(
    ("s", "result"),
    [
        ("", []),
        (
            "A",
            [Token(T.NAME, "A")],
        ),
        (
            "A = ",
            [Token(T.NAME, "A"), Token(T.OP_EQ, "=")],
        ),
        (
            'A = "foo"',
            [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.STR, '"foo"')],
        ),
        ("A = 1", [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.INT, "1")]),
        (
            "A = 1 OR A = 2",
            [
                Token(T.NAME, "A"),
                Token(T.OP_EQ, "="),
                Token(T.INT, "1"),
                Token(T.OR, "OR"),
                Token(T.NAME, "A"),
                Token(T.OP_EQ, "="),
                Token(T.INT, "2"),
            ],
        ),
        (
            "(A = 1)",
            [
                Token(T.LPAREN, "("),
                Token(T.NAME, "A"),
                Token(T.OP_EQ, "="),
                Token(T.INT, "1"),
                Token(T.RPAREN, ")"),
            ],
        ),
        (
            "A > 1",
            [
                Token(T.NAME, "A"),
                Token(T.OP_GT, ">"),
                Token(T.INT, "1"),
            ],
        ),
        (
            "A >= 1",
            [
                Token(T.NAME, "A"),
                Token(T.OP_GTE, ">="),
                Token(T.INT, "1"),
            ],
        ),
        (
            "A < 1",
            [
                Token(T.NAME, "A"),
                Token(T.OP_LT, "<"),
                Token(T.INT, "1"),
            ],
        ),
        (
            "A <= 1",
            [
                Token(T.NAME, "A"),
                Token(T.OP_LTE, "<="),
                Token(T.INT, "1"),
            ],
        ),
        (
            'A ~ "foo"',
            [
                Token(T.NAME, "A"),
                Token(T.OP_MATCH, "~"),
                Token(T.STR, '"foo"'),
            ],
        ),
        (
            "ANDX ORY",
            [
                Token(T.NAME, "ANDX"),
                Token(T.NAME, "ORY"),
            ],
        ),
        (
            '"',
            [
                Token(T.STR_PREFIX, '"'),
            ],
        ),
        (
            '"Foo',
            [
                Token(T.STR_PREFIX, '"Foo'),
            ],
        ),
        (
            "AND",
            [
                Token(T.AND, "AND"),
            ],
        ),
        (
            "and",
            [
                Token(T.AND, "and"),
            ],
        ),
        (
            "OR",
            [
                Token(T.OR, "OR"),
            ],
        ),
        (
            "or",
            [
                Token(T.OR, "or"),
            ],
        ),
        (
            "TRUE",
            [
                Token(T.BOOL_TRUE, "TRUE"),
            ],
        ),
        (
            "True",
            [
                Token(T.BOOL_TRUE, "True"),
            ],
        ),
        (
            "true",
            [
                Token(T.BOOL_TRUE, "true"),
            ],
        ),
        (
            "FALSE",
            [
                Token(T.BOOL_FALSE, "FALSE"),
            ],
        ),
        (
            "False",
            [
                Token(T.BOOL_FALSE, "False"),
            ],
        ),
        (
            "false",
            [
                Token(T.BOOL_FALSE, "false"),
            ],
        ),
        (
            "2025-01-27",
            [
                Token(T.DATE_YMD, "2025-01-27"),
            ],
        ),
        (
            "2025-1-2",
            [
                Token(T.DATE_YMD, "2025-1-2"),
            ],
        ),
        (
            "1.1.2025",
            [
                Token(T.DATE_DMY, "1.1.2025"),
            ],
        ),
        (
            "01.01.2025",
            [
                Token(T.DATE_DMY, "01.01.2025"),
            ],
        ),
        (
            "Uncommon'é-but-valid-name.",
            [
                Token(T.NAME, "Uncommon'é-but-valid-name."),
            ],
        ),
        (
            "1,2,3",
            [
                Token(T.LIST_INT, "1,2,3"),
            ],
        ),
        (
            "1, 2, 3",
            [
                Token(T.LIST_INT, "1, 2, 3"),
            ],
        ),
        (
            "A != 2025-1-2",
            [
                Token(T.NAME, "A"),
                Token(T.OP_NE, "!="),
                Token(T.DATE_YMD, "2025-1-2"),
            ],
        ),
    ],
)
def test_tokenize(s: str, result: list[str]):
    assert get_tokens(s, skip_ws=True) == result


def test_tokenize_whitespace():
    assert get_tokens("A =    ", skip_ws=False) == [
        Token(T.NAME, "A"),
        Token(T.WS, " "),
        Token(T.OP_EQ, "="),
        Token(T.WS, "    "),
    ]
