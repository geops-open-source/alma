from dataclasses import dataclass
from enum import Enum, auto, unique

from sqlalchemy import String, cast, select
from sqlalchemy.orm import Session

from alma.constants import Language
from alma.models.gem import Gemeinde
from alma.models.grun import Nummerierungsbereich

from .core import (
    FIELD_CONFIG,
    OPERATORS,
    FieldCategory,
    FieldType,
    SearchField,
)
from .parser import Expression, Op, ParseError, Parser, State
from .tokenizer import InvalidToken, Tokenizer
from .translation import get_translated_codes, get_translated_fields, lookup_field

# Limit number of suggestions to AUTOSUGGEST_LIMIT items
AUTOSUGGEST_LIMIT = 20


@unique
class AutoSuggestType(Enum):
    """
    Type of suggested item.
    """

    FIELD_NAME = auto()
    OPERATOR = auto()
    VALUE = auto()


@dataclass
class AutoSuggestItem:
    """
    An entry in the list of suggestions with additional metadata.
    """

    type: AutoSuggestType
    value: str  # String value to offer as completion
    category: FieldCategory | None = None  # Only for AutoSuggestType.FIELD_NAME
    field_type: FieldType | None = None  # Only for AutoSuggestType.OPERATOR


def autosuggest_gemeinde(
    session: Session, lang: Language, infix: str = ""
) -> list[AutoSuggestItem]:
    query = (
        select(Gemeinde.gemeinde)
        .where(Gemeinde.gemeinde.icontains(infix))
        .order_by(Gemeinde.gemeinde)
        .limit(AUTOSUGGEST_LIMIT)
    )
    results = session.scalars(query).all()
    return [AutoSuggestItem(AutoSuggestType.VALUE, f'"{name}"') for name in results]


def autosuggest_bfs_nr(
    session: Session, lang: Language, infix: str = ""
) -> list[AutoSuggestItem]:
    query = (
        select(Gemeinde.bfs_nummer)
        .order_by(Gemeinde.bfs_nummer)
        .limit(AUTOSUGGEST_LIMIT)
    )
    if infix:
        query = query.where(cast(Gemeinde.bfs_nummer, String).contains(infix))
    results = session.scalars(query).all()
    return [
        AutoSuggestItem(AutoSuggestType.VALUE, str(bfs_nummer))
        for bfs_nummer in results
    ]


def autosuggest_sprache(
    session: Session, lang: Language, infix: str = ""
) -> list[AutoSuggestItem]:
    return [
        AutoSuggestItem(AutoSuggestType.VALUE, f'"{lang.upper()}"') for lang in Language
    ]


def autosuggest_grundbuch_bezeichnung(
    session: Session, lang: Language, infix: str = ""
) -> list[AutoSuggestItem]:
    query = (
        select(Nummerierungsbereich.bezeichnung)
        .where(Nummerierungsbereich.bezeichnung.is_not(None))
        .where(Nummerierungsbereich.bezeichnung.icontains(infix))
        .distinct()
        .order_by(Nummerierungsbereich.bezeichnung)
        .limit(AUTOSUGGEST_LIMIT)
    )
    results = session.scalars(query).all()
    return [
        AutoSuggestItem(AutoSuggestType.VALUE, f'"{bezeichnung}"')
        for bezeichnung in results
    ]


# Mapping of search fields that have custom autosuggest functions for values
CUSTOM_AUTOSUGGEST_FUNCTIONS = {
    SearchField.GEMEINDE: autosuggest_gemeinde,
    SearchField.BFS_NR: autosuggest_bfs_nr,
    SearchField.SPRACHE: autosuggest_sprache,
    SearchField.GRUNDBUCH_BEZEICHNUNG: autosuggest_grundbuch_bezeichnung,
}


def autosuggest_fields(
    session: Session, prefix: str, lang: Language = Language.DE
) -> list[AutoSuggestItem]:
    """
    Auto-suggest search fields in the given language, filtered by `prefix` (may be empty).
    """
    items = get_translated_fields(session, prefix, lang=lang, limit=None)
    return [
        AutoSuggestItem(
            AutoSuggestType.FIELD_NAME,
            name,
            category,
        )
        for _, category, name in items
    ]


def autosuggest_operators(field_type: FieldType) -> list[AutoSuggestItem]:
    """
    Auto-suggest operators based on the field type.
    """
    operators = OPERATORS.get(field_type, [])
    return [
        AutoSuggestItem(AutoSuggestType.OPERATOR, op, field_type=field_type)
        for op in operators
    ]


def autosuggest_values(
    session: Session,
    name: SearchField,
    type: FieldType,
    lang: Language,
    infix: str = "",
) -> list[AutoSuggestItem]:
    """
    Autosuggest translated code values for the given field name, field type and language.

    Optionally filter values by `infix`.
    """
    if custom_function := CUSTOM_AUTOSUGGEST_FUNCTIONS.get(name):
        return custom_function(session, lang=lang, infix=infix)
    if type == FieldType.BOOL:
        return [
            AutoSuggestItem(AutoSuggestType.VALUE, "TRUE"),
            AutoSuggestItem(AutoSuggestType.VALUE, "FALSE"),
        ]
    elif type != FieldType.CODE:
        return []

    translated_codes = get_translated_codes(
        session, name, infix=infix, lang=lang, limit=AUTOSUGGEST_LIMIT
    )

    return [
        AutoSuggestItem(AutoSuggestType.VALUE, f'"{value}"')
        for value in translated_codes
    ]


def autosuggest(
    session: Session, input: str, lang: Language = Language.DE
) -> list[AutoSuggestItem]:
    """
    Generate a list of suggestions based on the given input string and language.
    """
    parser = Parser(Tokenizer(input))
    try:
        parser.parse(partial=True)  # Don't require a complete search string
    except (InvalidToken, ParseError):
        return []

    # Generate completions based on the current parser state
    match parser.state:
        case State.START:
            # Expected: Start of a new expression
            # (Empty input, or after AND, OR, ')')
            if (
                not input
                or input.endswith(" ")
                or (parser.result and parser.result[-1] == Op.LPAREN)
            ):
                return autosuggest_fields(session, "", lang=lang)
        case State.OPERATOR:
            # Expected: Comparison operator (in expression)
            expr = parser.get_last_expr()
            assert expr
            if input.endswith(" "):
                # Input ends with '<field name> ' (with trailing space): Suggest operators
                if field_name := lookup_field(session, expr.name):
                    field = FIELD_CONFIG[field_name]
                    return autosuggest_operators(field.type)
            else:
                # Input ends with '<field name>' (no trailing space): Suggest field names
                # w/ prefix '<field name>'.
                return autosuggest_fields(session, expr.name, lang=lang)
        case State.VALUE:
            # Expected: Value (in expression)
            expr = parser.get_last_expr()
            assert expr
            if input.endswith(" "):  # noqa: SIM102
                if field_name := lookup_field(session, expr.name):
                    field = FIELD_CONFIG[field_name]
                    return autosuggest_values(
                        session, field_name, field.type, lang=lang
                    )
        case State.PARTIAL_END:
            # At the end of a an incomplete expression, for example:
            #   '<file name> = "<text>' (note: no closing double quote).
            # Complete values w/ prefix '<text>'
            expr = parser.get_last_expr()
            assert expr
            assert expr.value is not None
            if field_name := lookup_field(session, expr.name):
                field = FIELD_CONFIG[field_name]
                return autosuggest_values(
                    session, field_name, field.type, infix=str(expr.value), lang=lang
                )

        case State.END:
            # At the end of an expression (after the value or a closing parenthesis).
            if input.endswith(" "):
                # Suggest AND, OR
                return [
                    AutoSuggestItem(AutoSuggestType.OPERATOR, "AND"),
                    AutoSuggestItem(AutoSuggestType.OPERATOR, "OR"),
                ]
            elif isinstance(parser.result[-1], Expression):
                # If the value is not a quoted string, suggest values with the existing value
                # as prefix (only for numbers)
                expr = parser.get_last_expr()
                assert expr
                assert expr.value is not None
                if field_name := lookup_field(session, expr.name):
                    field = FIELD_CONFIG[field_name]
                    if field.type == FieldType.NUMBER:
                        return autosuggest_values(
                            session,
                            field_name,
                            field.type,
                            infix=str(expr.value),
                            lang=lang,
                        )
    return []
