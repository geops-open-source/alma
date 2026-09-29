from dataclasses import dataclass
from typing import TypeAlias

from .core import SearchField
from .parser import Op, ValueType


@dataclass(frozen=True)
class TranslatedExpression:
    """
    An expression where field names and code values have been translated back to
    a SearchField constant and serialized code value ("code:<c_cli_id>:<code>") respectively.
    """

    name: SearchField
    operator: str
    value: ValueType


ParsedQuery: TypeAlias = list[TranslatedExpression | Op]


# Precedence: AND > OR
# All operators are left associative
PRECEDENCE = {
    Op.AND: 2,
    Op.OR: 1,
}


def order_expressions(input: ParsedQuery) -> ParsedQuery:
    """
    Convert a list of expressions joined with logical operators and optionally
    grouped by parentheses into a list in reverse polish notation (RPN), using
    the [Shunting yard algorithm][1].

    The output has no parentheses and is ordered for stack-based evaluation
    (right to left) with the correct precedence.

    [1]: https://en.wikipedia.org/wiki/Shunting_yard_algorithm
    """
    output: ParsedQuery = []
    op_stack: list[Op] = []

    for item in input:
        match item:
            case TranslatedExpression() as expr:
                output.append(expr)
            case Op.LPAREN as op:
                op_stack.append(op)
            case Op.RPAREN as op:
                while op_stack and op_stack[-1] != Op.LPAREN:
                    output.append(op_stack.pop())
                assert op_stack[-1] == Op.LPAREN
                op_stack.pop()
            case Op() as op:
                while (
                    op_stack
                    and op_stack[-1] != Op.LPAREN
                    # all operators are left associative
                    and PRECEDENCE[op_stack[-1]] >= PRECEDENCE[op]
                ):
                    output.append(op_stack.pop())
                op_stack.append(op)

    while op_stack:
        output.append(op_stack.pop())

    return output
