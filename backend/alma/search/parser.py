from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto, unique
from typing import Any, Protocol, TypeAlias

from .constants import MessageCode
from .tokenizer import T, Token

# All possible types of a value
ValueType: TypeAlias = str | int | bool | datetime | list[int]


class ParseError(Exception):
    def __init__(
        self,
        message: str,
        message_code: MessageCode,
        message_args: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.message_code = message_code
        self.message_args = message_args or {}


@unique
class Op(Enum):
    """
    Possible operators in the parse result.
    """

    AND = "AND"
    OR = "OR"
    LPAREN = "("
    RPAREN = ")"


@dataclass(frozen=True)
class Expression:
    """
    A (possibly incomplete) parsed expression.

    An expression always contains at least the field name.
    """

    name: str
    operator: str | None
    value: ValueType | None

    def is_complete(self) -> bool:
        """
        Return if the expression is complete (all values are present).
        """
        return self.operator is not None and self.value is not None

    def is_partial(self) -> bool:
        """
        Return if the expression is incomplete (operator and/or value are missing).
        """
        return not self.is_complete()


@unique
class State(Enum):
    """
    The parser state
    """

    START = auto()  # Start of expression expected.
    OPERATOR = auto()  # Operator expected (in expression).
    VALUE = auto()  # Value expected (in expression).
    END = auto()  # After end of expression.
    PARTIAL_END = auto()  # After end of partial expression.


@dataclass
class ExpressionContainer:
    """
    Container for the expression currently being parsed.

    Unlike `Expression`, this is mutable and can be assembled step by step.
    """

    name: str | None = None
    operator: str | None = None
    value: ValueType | None = None

    def clear(self) -> None:
        """
        Clear all collected values.
        """
        self.name = None
        self.operator = None
        self.value = None

    def get_expr(self) -> Expression | None:
        """
        Get an `Expression` object based on the currently collected values.
        """
        if self.name is None:
            return None

        return Expression(
            name=self.name,
            operator=self.operator,
            value=self.value,
        )


class TokenizerProto(Protocol):
    def get_next_token(self) -> Token | None: ...


class Parser:
    """
    Parses a token stream into a parse result.

    The result contains only expressions and a limited set of operators (AND, OR, parentheses).
    """

    def __init__(self, tokenizer: TokenizerProto):
        self.tokenizer = tokenizer  # The tokenizer from which to pull tokens
        self.state = State.START  # The current parser state
        self.paren_level = 0
        self.current_expr = ExpressionContainer()
        self.result: list[Op | Expression] = []  # The parse result

    def parse(self, partial: bool = False) -> None:
        """
        Get tokens from the tokenizer and generate the parse result.

        When `partial` is False, the input needs to represent a complete search string, i.e.
        no incomplete expressions, and correctly nested parentheses.

        When `partial` is True, the *last* expression encountered is allowed to be incomplete,
        and parentheses are not required to be closed.
        """
        while token := self.tokenizer.get_next_token():
            if token.type == T.WS:
                continue  # skip all whitespace
            match self.state:
                case State.START:
                    match token.type:
                        case T.LPAREN:
                            self.paren_level += 1
                            self.result.append(Op.LPAREN)
                        case T.NAME:
                            self.current_expr.name = token.value
                            self.state = State.OPERATOR
                        case _:
                            raise ParseError(
                                f"Expected LPAREN or NAME, got {token}",
                                message_code=MessageCode.ExpectedOpeningParenOrName,
                                message_args={"context": token.value},
                            )
                case State.OPERATOR:
                    match token.type:
                        case (
                            T.OP_EQ
                            | T.OP_NE
                            | T.OP_MATCH
                            | T.OP_GT
                            | T.OP_GTE
                            | T.OP_LT
                            | T.OP_LTE
                        ):
                            self.current_expr.operator = token.value
                            self.state = State.VALUE
                        case _:
                            raise ParseError(
                                f"Expected Operator, got {token}",
                                message_code=MessageCode.ExpectedOperator,
                                message_args={"context": token.value},
                            )
                case State.VALUE:
                    match token.type:
                        case T.INT:
                            self.current_expr.value = int(token.value)
                            self.state = State.END
                        case T.LIST_INT:
                            self.current_expr.value = [
                                int(s) for s in token.value.split(",")
                            ]
                            self.state = State.END
                        case T.DATE_DMY:
                            self.current_expr.value = datetime.strptime(
                                token.value, "%d.%m.%Y"
                            )
                            self.state = State.END
                        case T.DATE_YMD:
                            self.current_expr.value = datetime.strptime(
                                token.value, "%Y-%m-%d"
                            )
                            self.state = State.END
                        case T.STR:
                            # drop surrounding quotes
                            self.current_expr.value = token.value[1:-1]
                            self.state = State.END
                        case T.STR_PREFIX:
                            if partial:
                                # drop leading quote
                                self.current_expr.value = token.value[1:]
                                self.state = State.PARTIAL_END
                            else:
                                raise ParseError(
                                    f"Missing closing quote at {token.value}",
                                    message_code=MessageCode.UnterminatedString,
                                    message_args={"context": token.value},
                                )
                        case T.BOOL_TRUE:
                            self.current_expr.value = True
                            self.state = State.END
                        case T.BOOL_FALSE:
                            self.current_expr.value = False
                            self.state = State.END
                        case _:
                            raise ParseError(
                                f"Expected field value, got {token}",
                                message_code=MessageCode.ExpectedValue,
                                message_args={"context": token.value},
                            )
                case State.END:
                    if expr := self.current_expr.get_expr():
                        self.result.append(expr)
                        self.current_expr.clear()

                    match token.type:
                        case T.RPAREN:
                            self.paren_level -= 1
                            if self.paren_level < 0:
                                raise ParseError(
                                    "Missing opening parenthesis",
                                    message_code=MessageCode.UnexpectedClosingParen,
                                    message_args={"context": token.value},
                                )
                            self.result.append(Op.RPAREN)
                        case T.AND:
                            self.result.append(Op.AND)
                            self.state = State.START
                        case T.OR:
                            self.result.append(Op.OR)
                            self.state = State.START
                        case _:
                            raise ParseError(
                                f"Expected RPAREN, AND or OR, got {token}",
                                message_code=MessageCode.ExpectedClosingParenOrLogicalOperator,
                                message_args={"context": token.value},
                            )
                case State.PARTIAL_END:
                    raise ParseError(
                        f"Internal error: Invalid state: {self.state}",
                        message_code=MessageCode.InternalError,
                    )
                case _:  # pyright: ignore[reportUnnecessaryComparison]
                    raise ParseError(
                        f"Internal error: Invalid state: {self.state}",
                        message_code=MessageCode.InternalError,
                    )

        if not partial:
            if self.state != State.END:
                raise ParseError(
                    "Incomplete expression",
                    message_code=MessageCode.IncompleteExpression,
                )

            if self.paren_level != 0:
                raise ParseError(
                    "Missing closing parenthesis",
                    message_code=MessageCode.ParenNotClosed,
                )

        if expr := self.current_expr.get_expr():
            self.result.append(expr)

    def get_last_expr(self) -> Expression | None:
        """
        Get the last (possibly incomplete) expression from the parse result.
        """
        return next(
            (e for e in reversed(self.result) if isinstance(e, Expression)), None
        )
