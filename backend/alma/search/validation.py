from datetime import datetime
from typing import Any, Self

from sqlalchemy.orm import Session

from .advanced import ParsedQuery, TranslatedExpression
from .constants import MessageCode
from .core import (
    FIELD_CONFIG,
    OPERATORS,
    FieldConfig,
    FieldType,
    SearchField,
)
from .parser import Expression, Op, ParseError, Parser, ValueType
from .tokenizer import InvalidToken, Tokenizer
from .translation import lookup_code, lookup_field


class ValidationError(Exception):
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

    @classmethod
    def from_parse_error(cls, e: ParseError) -> Self:
        return cls(
            message=f"Syntax error: {e.message}",
            message_code=e.message_code,
            message_args=e.message_args,
        )


def validate_field_name(session: Session, expr: Expression) -> SearchField:
    # TODO use one query to look up all field names at once
    field_name = lookup_field(session, expr.name)
    if field_name is None:
        raise ValidationError(
            f"Unknown field name: {expr.name}",
            message_code=MessageCode.UnknownField,
            message_args={"context": expr.name},
        )
    return field_name


def validate_operator(expr: Expression, field: FieldConfig) -> str:
    operators = OPERATORS.get(field.type, [])
    if expr.operator not in operators:
        raise ValidationError(
            f'Unsupported operator for field "{expr.name}": "{expr.operator}"',
            message_code=MessageCode.InvalidOperator,
            message_args={"field": expr.name, "context": expr.operator},
        )
    return expr.operator


def validate_value(
    session: Session, expr: Expression, field_name: SearchField, field: FieldConfig
) -> ValueType:
    # Validate value types
    match field.type:
        case FieldType.TEXT:
            if isinstance(expr.value, str):
                return expr.value
            else:
                raise ValidationError(
                    f'Unsupported value for field "{expr.name}": {expr.value}',
                    message_code=MessageCode.InvalidValue,
                    message_args={"field": expr.name, "context": expr.value},
                )
        case FieldType.CODE:
            # Validate code values
            # TODO use one query to look up all code values at once
            if isinstance(expr.value, str):
                if code := lookup_code(session, field_name, expr.value):
                    return str(code)
                else:
                    raise ValidationError(
                        f'Not a valid value for field "{expr.name}": "{expr.value}"',
                        message_code=MessageCode.InvalidValue,
                        message_args={"field": expr.name, "context": f'"{expr.value}"'},
                    )
            else:
                raise ValidationError(
                    f'Unsupported value for field "{expr.name}": {expr.value}',
                    message_code=MessageCode.InvalidValue,
                    message_args={"field": expr.name, "context": expr.value},
                )

        case FieldType.NUMBER:
            if isinstance(expr.value, int | float):
                return expr.value
            else:
                value = f'"{expr.value}"' if isinstance(expr.value, str) else expr.value
                raise ValidationError(
                    f'Unsupported value for field "{expr.name}": {value}',
                    message_code=MessageCode.InvalidValue,
                    message_args={"field": expr.name, "context": value},
                )
        case FieldType.DATE:
            if isinstance(expr.value, datetime):
                return expr.value
            else:
                value = f'"{expr.value}"' if isinstance(expr.value, str) else expr.value
                raise ValidationError(
                    f'Unsupported value for field "{expr.name}": {value}',
                    message_code=MessageCode.InvalidValue,
                    message_args={"field": expr.name, "context": value},
                )
        case FieldType.BOOL:
            if expr.value in (True, False):
                return expr.value
            else:
                value = f'"{expr.value}"' if isinstance(expr.value, str) else expr.value
                raise ValidationError(
                    f'Unsupported value for field "{expr.name}": {value}',
                    message_code=MessageCode.InvalidValue,
                    message_args={"field": expr.name, "context": value},
                )
        case FieldType.BBOX:
            if (
                isinstance(expr.value, list)
                and len(expr.value) == 4
                and all(isinstance(i, int) for i in expr.value)  # pyright: ignore[reportUnnecessaryIsInstance]
            ):
                return expr.value
            value = (
                ", ".join(str(x) for x in expr.value)
                if isinstance(expr.value, list)
                else expr.value
            )
            raise ValidationError(
                f'Unsupported value for field "{expr.name}": {expr.value}',
                message_code=MessageCode.InvalidValue,
                message_args={"field": expr.name, "context": expr.value},
            )

    raise RuntimeError(f"Validation for value {expr.value!r} returned no result")


def validate(session: Session, query: str) -> ParsedQuery:
    """
    Validate a search string and return the parsed and translated result.

    Raises ValidationError if the string is syntactially or otherwise invalid.
    """
    parser = Parser(Tokenizer(query))
    try:
        parser.parse()
    except InvalidToken as e:
        raise ValidationError(
            message=str(e),
            message_code=MessageCode.InvalidToken,
            message_args={"context": e.token},
        )
    except ParseError as e:
        raise ValidationError.from_parse_error(e)

    result: ParsedQuery = []
    for item in parser.result:
        match item:
            case Expression() as expr:
                # Validate expression
                field_name = validate_field_name(session, expr)
                field = FIELD_CONFIG[field_name]

                translated_expr = TranslatedExpression(
                    name=field_name,
                    operator=validate_operator(expr, field),
                    value=validate_value(session, expr, field_name, field),
                )
                result.append(translated_expr)
            case Op() as op:
                result.append(op)

    return result
