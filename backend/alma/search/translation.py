from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from alma.constants import Language
from alma.models.codes import Code
from alma.models.translations import Translation
from alma.search.advanced import Op, ParsedQuery, TranslatedExpression, ValueType

from .core import CODELISTE_LOOKUP, FIELD_CONFIG, FieldCategory, FieldType, SearchField


def lookup_field(session: Session, translation: str) -> SearchField | None:
    """
    Look up a search field by its translated name (the name can be in any language).
    """
    # TODO add partial index to translations table to speed up this query
    query = select(Translation.key.distinct()).where(
        Translation.key.startswith("search.field."),
        func.lower(Translation.value) == translation.lower(),
    )
    key = session.scalars(query).one_or_none()
    if key is None:
        return None
    return SearchField(key.removeprefix("search.field."))


def translate_search_field(
    session: Session, field_name: SearchField, lang: Language
) -> str:
    key = f"search.field.{field_name}"
    query = select(Translation.value).where(
        Translation.key == key, Translation.locale == lang
    )
    return session.scalars(query).one()


def get_translated_fields(
    session: Session,
    prefix: str,
    lang: Language = Language.DE,
    limit: int | None = None,
) -> list[tuple[SearchField, FieldCategory, str]]:
    """
    Get category and translated name of search fields that match a prefix.
    """
    query = select(
        Translation.key,
        Translation.value,
    ).where(
        Translation.key.startswith("search.field."),
        Translation.locale == lang.value,
        Translation.value.istartswith(prefix),
    )
    if limit:
        query = query.limit(limit)
    rows = session.execute(query).all()
    field_names = [
        (SearchField(key.removeprefix("search.field.")), str(value))
        for key, value in rows
    ]
    field_names.sort(key=lambda item: (FIELD_CONFIG[item[0]].category.value, item[1]))
    return [(key, FIELD_CONFIG[key].category, value) for key, value in field_names]


def lookup_code(session: Session, name: SearchField, translation: str) -> Code | None:
    """
    Look up a Code object for a search field by its translated name.
    """
    c_cli_ids = CODELISTE_LOOKUP[name]
    assert c_cli_ids
    # TODO add partial index to translations table to speed up this query
    query = (
        # DISTINCT because a code can have the same translations in multiple languages.
        select(Code)
        .distinct()
        .join_from(Code, Translation, Code.search_key() == Translation.key)
        .where(
            Code.c_cli_id.in_(c_cli_ids),
            func.lower(Translation.value) == translation.lower(),
        )
    )
    return session.scalars(query).one_or_none()


def format_value(
    session: Session, field_name: SearchField, value: ValueType, lang: Language
) -> str:
    """
    Format a value for output in a formatted search string.
    """
    field_type = FIELD_CONFIG[field_name].type
    if field_type is FieldType.CODE:
        translation = translate_code(session, str(value), lang=lang)
        return f'"{translation}"'
    else:
        match value:
            case bool():
                return "TRUE" if value else "FALSE"
            case int():
                return str(value)
            case datetime():
                return value.strftime("%d.%m.%Y")
            case list():
                assert all(isinstance(x, int) for x in value)
                return ",".join(str(x) for x in value)
            case str():
                return f'"{value}"'
    return ""


def translate_code(session: Session, value: str, lang: Language) -> str:
    query = select(Translation.value).where(
        Translation.key == value,
        Translation.locale == lang,
    )
    return session.scalars(query).one()


def get_translated_codes(
    session: Session,
    name: SearchField,
    infix: str,
    lang: Language,
    limit: int | None = None,
) -> list[str]:
    """
    Get translated names of codes for a given search field that match a prefix.
    """
    result: list[str] = []
    for c_cli_id in CODELISTE_LOOKUP[name]:
        # TODO group values by code list if there are multiple options
        # TODO deal w/ missing translations
        query = (
            select(Translation.value)
            .join_from(Code, Translation, Code.search_key() == Translation.key)
            .where(
                Code.c_cli_id == c_cli_id,
                Translation.locale == lang,
            )
            .order_by(Translation.value)
        )
        if infix:
            query = query.where(Translation.value.icontains(infix))
        if limit:
            query = query.limit(limit)
        values = session.scalars(query).all()
        result.extend(values)

    return result[:limit] if limit else result


def build_query_string(
    session: Session, parsed_query: ParsedQuery, lang: Language
) -> str:
    """
    Turn a parsed query back into a search string in the given language.
    """
    query_parts: list[str] = []

    for item in parsed_query:
        match item:
            case TranslatedExpression(field_name, operator, value):
                query_parts.append(
                    translate_search_field(session, field_name, lang=lang)
                )
                query_parts.append(operator)
                query_parts.append(format_value(session, field_name, value, lang=lang))
            case Op():
                query_parts.append(item.value)

    return " ".join(query_parts)
