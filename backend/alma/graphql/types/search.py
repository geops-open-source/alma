from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Self, cast

import strawberry
from sqlalchemy import select
from strawberry.scalars import JSON

import alma.search
import alma.search.export
from alma.graphql.types.vflz import Language, Vflz
from alma.models import auth as auth_models
from alma.models import search as search_models
from alma.search.advanced import ParsedQuery
from alma.search.constants import DASHBOARD_SAVED_SEARCH_SETTINGS_KEY
from alma.search.serialization import deserialize_query
from alma.search.translation import build_query_string

from ..scalars import GeoJSONFeatureCollection
from ..utils.schema import Info, to_id
from .auth import User

# See https://github.com/strawberry-graphql/strawberry/issues/3543
if TYPE_CHECKING:
    AutoSuggestType = alma.search.AutoSuggestType
    SearchField = alma.search.SearchField
    FieldType = alma.search.FieldType
    FieldCategory = alma.search.FieldCategory
    ExportFormat = alma.search.export.ExportFormat
    ExportStatus = alma.search.export.ExportStatus
else:
    AutoSuggestType = strawberry.enum(alma.search.AutoSuggestType)
    SearchField = strawberry.enum(alma.search.SearchField)
    FieldType = strawberry.enum(alma.search.FieldType)
    FieldCategory = strawberry.enum(
        alma.search.FieldCategory, name="SearchFieldCategory"
    )
    ExportFormat = strawberry.enum(
        alma.search.export.ExportFormat, name="SearchExportFormat"
    )
    ExportStatus = strawberry.enum(
        alma.search.export.ExportStatus, name="SearchExportStatus"
    )


@strawberry.type
class AutoSuggestItem:
    type: AutoSuggestType
    value: str
    category: FieldCategory | None  # only for AutoSuggestType.FIELD_NAME
    field_type: FieldType | None  # only for AutoSuggestType.OPERATOR

    @classmethod
    def from_obj(cls, obj: alma.search.AutoSuggestItem) -> Self:
        return cls(
            type=obj.type,
            value=obj.value,
            category=obj.category,
            field_type=obj.field_type,
        )


@strawberry.type
class FieldInfo:
    field: SearchField
    name: str
    type: FieldType


@strawberry.type
class SearchFieldName:
    field: SearchField
    category: FieldCategory
    name: str


@strawberry.input
class SearchFilter:
    field: SearchField
    value: JSON  # to allow int, str, bool, lists


@strawberry.input
class SortItemInput:
    field: SearchField
    reverse: bool = False


@strawberry.type
class SortItem:
    field: SearchField
    reverse: bool


@strawberry.type
class TabularSearchResult:
    num_pages: int
    num_results_total: int
    results: list[JSON]


@strawberry.type
class GraphSearchResult:
    num_pages: int
    num_results_total: int
    results: list[Vflz]


@strawberry.type
class GeoSearchResult:
    num_results_total: int
    _get_zentroid: strawberry.Private[Callable[[], str]]
    _get_vflgeo: strawberry.Private[Callable[[], str]]

    @strawberry.field
    def zentroid(self, info: Info) -> GeoJSONFeatureCollection:
        return cast(GeoJSONFeatureCollection, self._get_zentroid())

    @strawberry.field
    def vflgeo(self, info: Info) -> GeoJSONFeatureCollection:
        return cast(GeoJSONFeatureCollection, self._get_vflgeo())


@strawberry.type
class SearchResult:
    # Wrap result and hits in callables to make them lazy, to avoid computing both for every query.
    # Search can be expensive and a given graphql query will only query one of them at a time.
    _get_tabular_result: strawberry.Private[Callable[[], TabularSearchResult]]
    _get_graph_result: strawberry.Private[Callable[[], GraphSearchResult]]
    _get_geo_result: strawberry.Private[
        Callable[[tuple[float, float, float, float] | None], GeoSearchResult]
    ]
    page: int
    per_page: int
    direct_match: bool

    @strawberry.field
    def tabular(self, info: Info) -> TabularSearchResult:
        return self._get_tabular_result()

    @strawberry.field
    def graph(self, info: Info) -> GraphSearchResult:
        return self._get_graph_result()

    @strawberry.field
    def geo(
        self, info: Info, extent: list[float] | None = strawberry.UNSET
    ) -> GeoSearchResult:
        validated_extent: tuple[float, float, float, float] | None = None
        if not (extent is None or extent is strawberry.UNSET):
            xmin, ymin, xmax, ymax = extent
            validated_extent = (xmin, ymin, xmax, ymax)

        return self._get_geo_result(validated_extent)


@strawberry.type
class SavedSearch:
    _search: strawberry.Private[search_models.Search]
    parsed_query: strawberry.Private[ParsedQuery]
    saved_search_id: strawberry.ID
    name: str
    fields: list[SearchField]
    sort_by: list[SortItem]
    is_grouped: bool
    is_shared: bool
    user: User

    @strawberry.field
    def show_on_dashboard(self, info: Info) -> bool:
        session = info.context.db
        user_setting = session.scalars(
            select(auth_models.UserSetting).where(
                auth_models.UserSetting.key == DASHBOARD_SAVED_SEARCH_SETTINGS_KEY,
                auth_models.UserSetting.user_id == info.context.user.id,
            )
        ).one_or_none()
        if not user_setting:
            return False
        return self._search.search_id in user_setting.value

    @strawberry.field
    def query(self, info: Info, lang: Language) -> str:
        session = info.context.db
        return build_query_string(session, self.parsed_query, lang)

    @classmethod
    def from_db(cls, obj: search_models.Search) -> Self:
        parsed_query = deserialize_query(obj.query)
        return cls(
            _search=obj,
            parsed_query=parsed_query,
            saved_search_id=to_id(obj.search_id),
            name=obj.name,
            fields=[SearchField(f) for f in obj.fields],
            sort_by=[
                SortItem(field=SearchField(sb["field"]), reverse=sb["reverse"])
                for sb in obj.sort_by
            ],
            is_grouped=obj.is_grouped,
            is_shared=obj.is_shared,
            user=User.from_db(obj.user),
        )


@strawberry.type
class SearchExport:
    export_id: strawberry.ID
    format: ExportFormat
    lang: Language
    status: ExportStatus
    started_at: datetime
    finished_at: datetime | None = None
    download_url: str | None = None

    @classmethod
    def from_db(cls, obj: search_models.SearchExport) -> Self:
        return cls(
            export_id=strawberry.ID(obj.export_id),
            format=ExportFormat(obj.format),
            lang=obj.lang,
            status=ExportStatus(obj.status),
            started_at=obj.started_at,
            finished_at=obj.finished_at,
            download_url=f"/api/exports/search/{obj.export_id}",
        )


@strawberry.input
class CreateSavedSearchInput:
    name: str
    query: str
    fields: list[SearchField]
    sort_by: list[SortItemInput]
    is_grouped: bool
    show_on_dashboard: bool
    is_shared: bool


@strawberry.input
class AddSearchResultsToPoolInput:
    pool_id: strawberry.ID
    query: str


@strawberry.input
class ExportSearchInput:
    query: str
    fields: list[SearchField]
    sort_by: list[SortItemInput]
    format: ExportFormat
    lang: Language


@strawberry.input
class UpdateSavedSearchInput:
    saved_search_id: strawberry.ID
    name: str
    is_shared: bool
    show_on_dashboard: bool
