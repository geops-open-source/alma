from datetime import datetime

import pytest

from alma.search.parser import Expression, Op, Parser, State
from alma.search.tokenizer import Token
from alma.search.tokenizer import TokenType as T


class FakeTokenizer:
    def __init__(self, tokens: list[Token]):
        self.tokens = list(reversed(tokens))

    def get_next_token(self) -> Token | None:
        if self.tokens:
            return self.tokens.pop()
        return None


def test_parse_expr_int():
    tokens = [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.INT, "1")]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [Expression("A", "=", 1)]


def test_parse_expr_bool():
    tokens = [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.BOOL_TRUE, "TRUE")]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [Expression("A", "=", True)]


def test_parse_expr_date_ymd():
    tokens = [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.DATE_YMD, "2025-01-02")]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [Expression("A", "=", datetime(2025, 1, 2))]


def test_parse_expr_date_mdy():
    tokens = [Token(T.NAME, "A"), Token(T.OP_EQ, "="), Token(T.DATE_DMY, "02.01.2025")]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [Expression("A", "=", datetime(2025, 1, 2))]


def test_parse_expr_list():
    tokens = [
        Token(T.NAME, "A"),
        Token(T.OP_EQ, "="),
        Token(T.INT, "1"),
        Token(T.OR, "OR"),
        Token(T.NAME, "B"),
        Token(T.OP_EQ, "="),
        Token(T.INT, "2"),
    ]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [
        Expression("A", "=", 1),
        Op.OR,
        Expression("B", "=", 2),
    ]


def test_parse_expr_list_parens():
    # Expr1 AND (Expr2 OR Expr3)
    tokens = [
        Token(T.NAME, "A"),
        Token(T.OP_EQ, "="),
        Token(T.INT, "1"),
        Token(T.AND, "AND"),
        Token(T.LPAREN, "("),
        Token(T.NAME, "B"),
        Token(T.OP_EQ, "="),
        Token(T.INT, "2"),
        Token(T.OR, "OR"),
        Token(T.NAME, "C"),
        Token(T.OP_EQ, "="),
        Token(T.INT, "3"),
        Token(T.RPAREN, ")"),
    ]

    parser = Parser(FakeTokenizer(tokens))
    parser.parse()

    assert parser.result == [
        Expression("A", "=", 1),
        Op.AND,
        Op.LPAREN,
        Expression("B", "=", 2),
        Op.OR,
        Expression("C", "=", 3),
        Op.RPAREN,
    ]


@pytest.mark.parametrize(
    ("tokens", "state", "result"),
    [
        (
            [Token(T.NAME, "A"), Token(T.WS, " ")],
            State.OPERATOR,
            [Expression("A", None, None)],
        ),
        (
            [Token(T.NAME, "A"), Token(T.WS, " "), Token(T.OP_EQ, "=")],
            State.VALUE,
            [Expression("A", "=", None)],
        ),
    ],
)
def test_parse_partial_query(
    tokens: list[Token], state: State, result: list[Op | Expression]
):
    parser = Parser(FakeTokenizer(tokens))
    parser.parse(partial=True)

    assert parser.state == state
    assert parser.result == result
