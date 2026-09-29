import math
import typing
import warnings
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy import (
    Select,
    SQLColumnExpression,
    String,
    and_,
    any_,
    cast,
    desc,
    func,
    or_,
    select,
    text,
    union,
)
from sqlalchemy.dialects.postgresql import JSONB, array
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session, aliased

from alma.constants import LV_95_SRID, Language
from alma.models import codes
from alma.models.auth import Permission, User
from alma.models.vflz import (
    Beurteilung,
    EvaluationStatusData,
    VflGeo,
    Vflz,
)

from .advanced import Op, ParsedQuery, TranslatedExpression, order_expressions
from .core import (
    CODE_TRANSLATION_ALIASES,
    FIELD_CONFIG,
    FTS_CONFIG,
    FTS_FIELDS,
    FTS_JOIN_FIELDS,
    JOIN_PATH,
    JOINS,
    FieldCategory,
    FieldType,
    JoinType,
    SearchField,
)
from .validation import validate


@dataclass
class ResultPage:
    results: list[tuple[Any, ...]]
    num_pages: int
    num_results_total: int


def _evaluate_advanced_query(stack: ParsedQuery) -> SQLColumnExpression[Any]:
    """
    Evaluate a parsed search query.

    Returns an expression to use in the WHERE clause.
    """
    item = stack.pop()
    match item:
        case Op.AND:
            left = _evaluate_advanced_query(stack)
            right = _evaluate_advanced_query(stack)
            return and_(left, right)
        case Op.OR:
            left = _evaluate_advanced_query(stack)
            right = _evaluate_advanced_query(stack)
            return or_(left, right)
        case TranslatedExpression(field_name, operator, value):
            field = FIELD_CONFIG[field_name]
            # Allow comparison between text columns an integer values (e.g. PLZ)
            if field.type == FieldType.NUMBER:
                value = str(value)
            match operator:
                case "=":
                    if field.type == FieldType.TEXT:
                        return func.lower(field.expr) == func.lower(value)
                    elif field.type == FieldType.BBOX:
                        assert isinstance(value, list)
                        xmin, ymin, xmax, ymax = value
                        return field.expr.op("&&")(
                            func.ST_MakeEnvelope(xmin, ymin, xmax, ymax, LV_95_SRID)
                        )
                    else:
                        return field.expr == value
                case "!=":
                    return field.expr != value
                case "<":
                    return field.expr < value
                case "<=":
                    return field.expr <= value
                case ">":
                    return field.expr > value
                case ">=":
                    return field.expr >= value
                case "~":
                    return field.expr.icontains(value)
                case _:
                    raise ValueError(f"Invalid operator: {operator!r}")
        case _:
            raise ValueError(f"Invalid item on stack: {item!r}")


def check_field_permissions(fields: list[SearchField], user: User) -> None:
    if not user.has_permission(Permission.VIEW_PROCESS) and (
        any(f for f in fields if FIELD_CONFIG[f].category == FieldCategory.GESCHAEFT)
    ):
        raise PermissionError("error.Permissions.SearchQuery")


def quick_search(session: Session, search: str) -> list[int] | None:
    """
    Quick search

    Check for direct match against Vflz.combined_id or Vflz.bezeichnung without any filters

    Returns a vflz_id if the search string matches the combined_id / bezeichnung exactly and unambiguously, i.e.
    the search string does not also match the start of another combined_id / bezeichnung.
    """
    query_combined_id = select(
        Vflz.vflz_id, func.lower(Vflz.combined_id) == func.lower(search)
    ).where(Vflz.combined_id.istartswith(search), Vflz.is_current)

    query_bezeichnung = select(
        Vflz.vflz_id, func.lower(Vflz.bezeichnung) == func.lower(search)
    ).where(Vflz.bezeichnung.istartswith(search), Vflz.is_current)

    rows_combined_id = session.execute(query_combined_id).all()
    rows_bezeichnung = session.execute(query_bezeichnung).all()

    results: list[int] = []
    if len(rows_combined_id) == 1:
        vflz_id, exact_match = rows_combined_id[0]
        if exact_match:
            results.append(vflz_id)

    if len(rows_bezeichnung) == 1:
        vflz_id, exact_match = rows_bezeichnung[0]
        if exact_match:
            results.append(vflz_id)

    return results or None


def simple_search(
    session: Session,
    user: User,
    search: str,
    filters: Sequence[tuple[SearchField, Any]] | None = None,
    lang: Language = Language.DE,
) -> set[int]:
    """
    Simple search

    Search string is matched against a range of fields and filters are provided as a list.
    """
    filters = filters or []
    join_fields = [field_name for field_name, _ in filters]
    check_field_permissions(join_fields, user)
    return execute_simple_search(session, search, filters, lang)


def filter_vflz_ids(
    session: Session,
    vflz_ids: set[int],
    filters: Sequence[tuple[SearchField, Any]] | None = None,
) -> set[int]:
    """
    Filters out the vflz_ids that do not match the filters provided. Returns the filtered set of vflz_ids.
    """
    if not filters:
        return set(vflz_ids)

    join_fields = [field_name for field_name, _ in filters]
    query = select(Vflz.vflz_id).where(Vflz.is_current, Vflz.vflz_id.in_(vflz_ids))
    query = _apply_joins(query=query, fields=join_fields)

    for field_name, value in filters:
        field = FIELD_CONFIG[field_name]
        match field.type:
            case FieldType.TEXT:
                # TODO we need to escape '%' in the query term.
                # Replace ILIKE search with FTS later.
                if isinstance(value, list):
                    patterns = [f"%{v}%" for v in typing.cast(list[Any], value)]
                    query = query.where(
                        field.expr.op("ILIKE")(any_(array[str](patterns)))
                    )
                else:
                    query = query.where(field.expr.icontains(value))
            case _:
                if isinstance(value, list):
                    query = query.where(field.expr.in_(typing.cast(list[Any], value)))
                else:
                    query = query.where(field.expr == value)

    with raise_on_cartesian_join():
        rows = session.execute(query).tuples().all()
        filtered_vflz_ids = set([row[0] for row in rows])
        return filtered_vflz_ids


def execute_simple_search(
    session: Session,
    search: str,
    filters: Sequence[tuple[SearchField, Any]] | None = None,
    lang: Language = Language.DE,
) -> set[int]:
    """Executes simple search query.

    The process is as follows:

    1. Apply full text search on each table with its own query. Add ilike condition. Return relevant vflz_ids.
    2. Apply union on all queries.
    3. Take the returned vflz_ids and apply joins based on filters provided.

    Since the index on the ts_vector expression can only be applied if we have only one to_tsvector
    `where` condition, we cannot merge the queries into one big query.
    """

    filters = filters or []
    fts_config = FTS_CONFIG[lang]

    lookups: list[SQLColumnExpression[Any]] = []
    search_fields: list[SearchField] = []
    queries: list[Select[Any]] = []

    # create queries
    if search:
        for expr, search_field in zip(FTS_FIELDS, FTS_JOIN_FIELDS):
            # Use FTS for word-based matching
            fts_condition = func.to_tsvector(fts_config, expr).op("@@")(
                func.plainto_tsquery(fts_config, search)
            )
            # ILIKE for substring matching
            ilike_condition = expr.ilike(f"%{search}%")

            lookups.append(fts_condition)
            search_fields.append(search_field)

            lookups.append(ilike_condition)
            search_fields.append(search_field)

        for lookup, search_field in zip(lookups, search_fields):
            queries.append(
                _apply_joins(
                    query=(select(Vflz.vflz_id).where(lookup, Vflz.is_current)),
                    fields=[search_field],
                )
            )
    else:
        queries = [select(Vflz.vflz_id).where(Vflz.is_current)]

    # create union and execute resulting query
    union_subquery = union(*queries).subquery()
    query = select(union_subquery.c.vflz_id)

    with raise_on_cartesian_join():
        rows = session.execute(query).tuples().all()
        vflz_ids = set([row[0] for row in rows])

    return filter_vflz_ids(session, vflz_ids, filters)


def execute_advanced_search(session: Session, parsed_query: ParsedQuery) -> set[int]:
    """
    Execute a parsed and validated advanced search query.
    """
    join_fields = [
        expr.name for expr in parsed_query if isinstance(expr, TranslatedExpression)
    ]
    query = select(Vflz.vflz_id).where(Vflz.is_current)  # only consider latest version
    query = _apply_joins(query, join_fields)

    stack = order_expressions(parsed_query)
    query = query.where(_evaluate_advanced_query(stack))
    assert not stack  # All items have been consumed

    with raise_on_cartesian_join():
        rows = session.execute(query).tuples().all()
        return set([row[0] for row in rows])


def advanced_search(session: Session, user: User, search: str) -> set[int]:
    """
    Advanced search

    Search expression is parsed from the search input
    """
    parsed_query = validate(session, search)
    join_fields = [
        expr.name for expr in parsed_query if isinstance(expr, TranslatedExpression)
    ]
    check_field_permissions(join_fields, user)
    return execute_advanced_search(session, parsed_query)


def get_search_results(
    session: Session,
    user: User,
    search: str,
    filters: Sequence[tuple[SearchField, Any]] | None = None,
    lang: Language = Language.DE,
    advanced: bool = False,
) -> tuple[set[int], bool]:
    """
    Get a list of Vflz IDs that match the search criteria.

    Args:
        search: Search string as entered by the user (can be empty).
        filters: List of `(field_name, value)` pairs.
        lang: Language used for FTS features like stop word detection and stemming.
        advanced: When True, the search is an advanced search, else a simple or quick search.

    Returns:
        A tuple of `(vflz_ids, direct_match)`. `direct_match` is true when the
        search was a simple search (advanced=False) and `search` matched an exact
        "Standortnummer", false otherwise.
    """
    search = search.strip()
    filters = filters or []

    if search:
        if advanced:
            return advanced_search(session, user, search), False
        else:
            check_field_permissions([field_name for field_name, _ in filters], user)
            vflz_ids = quick_search(session, search)
            if vflz_ids and (
                filtered_vflz_ids := filter_vflz_ids(session, set(vflz_ids), filters)
            ):
                return set(filtered_vflz_ids), True

    return simple_search(session, user, search, filters=filters, lang=lang), False


def _apply_joins(
    query: Select[Any],
    fields: Sequence[SearchField],
    for_order_by_lang: Language | None = None,
) -> Select[Any]:
    """
    Apply any joins to `query` that are necessary for filtering or sorting by `fields`.

    When `for_order_by_lang` is not None, additionally the translation table
    will be joined once for each field that has an entry in
    `CODE_TRANSLATION_ALIASES` using the language given.
    """
    # Set to keep track of which joins have already been applied.
    joins_applied: set[JoinType] = set()

    for field_name in fields:
        field = FIELD_CONFIG[field_name]
        joins = JOIN_PATH.get(field.join_type, []) + [field.join_type]
        for join in joins:
            if join not in joins_applied:
                query = JOINS[join](query)
                joins_applied.add(join)

        if for_order_by_lang and (aliases := CODE_TRANSLATION_ALIASES.get(field_name)):
            code_alias, translations_alias = aliases
            query = query.outerjoin(
                translations_alias,
                and_(
                    translations_alias.key == code_alias.search_key(),
                    translations_alias.locale == for_order_by_lang,
                ),
            )

    return query


@contextmanager
def raise_on_cartesian_join() -> Iterator[None]:
    """
    Context manager to turn sqlalchemy warnings about cartesian joins into exceptions.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            action="error",
            category=SAWarning,
            message=".*cartesian.*",
        )
        yield


def get_result_page(
    session: Session,
    vflz_ids: Iterable[int],
    fields: Sequence[SearchField],
    sort_by: Sequence[tuple[SearchField, bool]] | None = None,
    lang: Language = Language.DE,
    translate_codes: bool = False,
    include_geoms: bool = False,
    page: int = 1,
    per_page: int = 10,
) -> ResultPage:
    """
    Get a single page of tabular search results.

    Args:
        vflz_ids: The list of Vflz IDs as returned by `get_search_results`.

        fields: The list of field names which should be included in the output.

        sort_by: A list of `(field_name, reverse)` tuples that specify the sort order.

        lang: When sorting by code fields, the fields are actually sorted by
          the translated name of the code in this language.

        translate_codes: Whether or not to translate code values in the output
          according to `lang`. Used for search exports.

        include_geoms: Whether or not to add the Vfl geometry as the last
          column. Used for search exports.

        page, per_page: Return page number `page` containing `per_page` rows.
    """
    vflz_ids = sorted(set(vflz_ids))
    sort_by = sort_by or []

    order_by: list[SQLColumnExpression[Any]] = []
    for field_name, reverse in sort_by:
        if field_name in fields:
            if aliases := CODE_TRANSLATION_ALIASES.get(field_name):
                code_alias, translations_alias = aliases
                expr = func.coalesce(translations_alias.value, code_alias.search_key())
            else:
                expr = FIELD_CONFIG[field_name].expr
            order_by.append(desc(expr) if reverse else expr)

    # To guarantee a stable sort order, append fields not already listed in sort_by to ORDER BY
    for field_name in fields:
        if field_name not in [f for f, _ in sort_by]:
            order_by.append(FIELD_CONFIG[field_name].expr)

    expressions: list[SQLColumnExpression[Any]] = [
        func.row_number().over(order_by=order_by).label("row_id")
    ]
    for field_name in fields:
        if translate_codes and (aliases := CODE_TRANSLATION_ALIASES.get(field_name)):
            code_alias, translations_alias = aliases
            expr = func.coalesce(translations_alias.value, code_alias.search_key())
        else:
            expr = FIELD_CONFIG[field_name].expr
        expressions.append(expr)

    count_query = select(func.count()).where(Vflz.vflz_id.in_(vflz_ids))
    count_query = _apply_joins(count_query, fields=fields)

    results_query = select(*expressions).where(Vflz.vflz_id.in_(vflz_ids))

    if include_geoms:
        vflgeo_alias = aliased(VflGeo)
        results_query = results_query.outerjoin(Vflz.vflgeo.of_type(vflgeo_alias))
        results_query = results_query.add_columns(
            func.ST_AsEWKT(vflgeo_alias.wkb_geometry)
        )

    # we need the vflz_id to be in the search result to be able to fetch the vflz from the
    # database for fetching the evaluation status. If it is not present in the search query already
    # we need to add it.
    vflz_id_as_last_column = results_query.selected_columns.keys()[-1] == "vflz_id"
    if not vflz_id_as_last_column:
        results_query = results_query.add_columns(Vflz.vflz_id)

    results_query = _apply_joins(results_query, fields=fields, for_order_by_lang=lang)
    results_query = results_query.order_by(*order_by)
    results_query = results_query.limit(per_page).offset(per_page * (page - 1))

    with raise_on_cartesian_join():
        num_results_total = session.scalar(count_query)
        assert num_results_total is not None

    with raise_on_cartesian_join():
        rows = session.execute(results_query).tuples().all()

    formatted_result_rows = [
        (
            (
                _format_result_row(row)
                if vflz_id_as_last_column
                else _format_result_row(row[:-1])
            )
            + (
                EvaluationStatusData.from_vflz(
                    session, session.get_one(Vflz, row[-1])
                ).to_dict(),
            )
        )
        for row in rows
    ]

    return ResultPage(
        results=formatted_result_rows,
        num_pages=math.ceil(num_results_total / per_page),
        num_results_total=num_results_total,
    )


def _format_result_row(row: tuple[Any, ...]) -> tuple[str | int | bool | None, ...]:
    """
    Format row to include only JSON-serializable scalar types.
    """
    return tuple(
        [
            item if isinstance(item, str | int | bool | None) else str(item)
            for item in row
        ]
    )


def get_features_zentroid(
    session: Session,
    vflz_ids: Iterable[int],
    extent: tuple[float, float, float, float] | None = None,
) -> str:
    vflz_ids = sorted(set(vflz_ids))

    zentroid_features_query = (
        select(
            Vflz.vflz_id.label("vflzId"),
            codes.KbsInfo.color,
            Vflz.zentroid.label("geom"),
        )
        .select_from(Vflz)
        .outerjoin(Beurteilung)
        .outerjoin(
            codes.KbsInfo,
            and_(
                Beurteilung.h_bere_res_abwbewe == codes.KbsInfo.h_bere_res_abwbewe,
                Beurteilung.c_bere_res_abwbewe == codes.KbsInfo.c_bere_res_abwbewe,
            ),
        )
        .where(
            Vflz.vflz_id.in_(vflz_ids),
            Vflz.is_current,
            Vflz.zentroid.is_not(None),
        )
        .order_by(Vflz.vflz_id)
    )

    if extent is not None:
        zentroid_features_query = zentroid_features_query.where(
            Vflz.zentroid.op("&&")(func.ST_MakeEnvelope(*extent))
        )

    return _get_feature_collection(session, zentroid_features_query)


def get_features_vflgeo(
    session: Session,
    vflz_ids: Iterable[int],
    extent: tuple[float, float, float, float] | None = None,
) -> str:
    vflz_ids = sorted(set(vflz_ids))

    vflgeo_features_query = (
        select(
            Vflz.vflz_id.label("vflzId"),
            codes.KbsInfo.color,
            VflGeo.wkb_geometry.label("geom"),
        )
        .select_from(Vflz)
        .join(VflGeo)
        .outerjoin(Beurteilung)
        .outerjoin(
            codes.KbsInfo,
            and_(
                Beurteilung.h_bere_res_abwbewe == codes.KbsInfo.h_bere_res_abwbewe,
                Beurteilung.c_bere_res_abwbewe == codes.KbsInfo.c_bere_res_abwbewe,
            ),
        )
        .where(
            Vflz.vflz_id.in_(vflz_ids),
            Vflz.is_current,
        )
        .order_by(Vflz.vflz_id)
    )

    if extent is not None:
        vflgeo_features_query = vflgeo_features_query.where(
            VflGeo.wkb_geometry.op("&&")(func.ST_MakeEnvelope(*extent))
        )

    return _get_feature_collection(session, vflgeo_features_query)


def _get_feature_collection(session: Session, query: Select[Any]) -> str:
    geojson_query = select(
        cast(
            func.jsonb_build_object(
                "type",
                "FeatureCollection",
                "features",
                func.coalesce(
                    func.jsonb_agg(
                        cast(
                            func.ST_AsGeoJSON(
                                query.subquery("features"),
                            ),
                            JSONB,
                        )
                    ),
                    cast(text("'[]'"), JSONB),
                ),
            ),
            String,
        ).label("geojson")
    )

    geojson = session.scalar(geojson_query)
    assert geojson

    return geojson
